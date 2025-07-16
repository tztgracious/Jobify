package com.chatwaifu.mobile

import android.content.Context
import android.content.SharedPreferences
import android.util.Log
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.chatwaifu.chatgpt.ChatGPTNetService
import com.chatwaifu.chatgpt.ChatGPTResponseData
import com.chatwaifu.mobile.application.ChatWaifuApplication
import com.chatwaifu.mobile.data.Constant
import com.chatwaifu.mobile.data.VITSLoadStatus
import com.chatwaifu.mobile.ui.channellist.ChannelListBean
import com.chatwaifu.mobile.ui.common.ChatDialogContentUIState
import com.chatwaifu.mobile.utils.AssistantMessageManager
import com.chatwaifu.mobile.utils.LipsValueHandler
import com.chatwaifu.mobile.utils.LocalModelManager
import com.chatwaifu.translate.ITranslate
import com.chatwaifu.translate.baidu.BaiduTranslateService
import com.chatwaifu.vits.utils.SoundGenerateHelper
import kotlinx.coroutines.CancellableContinuation
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlin.coroutines.Continuation
import kotlin.coroutines.resume

/**
 * Description: main view model
 * Author: Voine
 * Date: 2023/2/18
 */
class ChatActivityViewModel : ViewModel() {
    companion object {
        private const val TAG = "ChatActivityViewModel"
        
        // Interview mode constants
        private const val INTERVIEW_QUESTIONS_COUNT = 3
        private const val EXTRA_INTERVIEW_MODE = "interview_mode"
    }

    enum class ChatStatus {
        DEFAULT,
        INTERVIEW_MODE,
        GENERATE_SOUND,
    }

    // Interview mode state
    private var isInterviewMode: Boolean = false
    private var currentInterviewQuestionIndex: Int = 0
    private var currentDocId: String? = null
    private val interviewQuestions = listOf(
        "Please introduce yourself and tell me about your background.",
        "What are your greatest strengths and how would they benefit this role?",
        "Describe a challenging project you worked on and how you overcame obstacles."
    )
    private val interviewAnswers = mutableListOf<String>()
    private val interviewTips = "Thank you for completing the interview! Here are some tips for your next interview:\n\n" +
            "• Practice your responses to common questions\n" +
            "• Research the company and role thoroughly\n" +
            "• Prepare specific examples from your experience\n" +
            "• Ask thoughtful questions about the position\n" +
            "• Follow up with a thank-you email after the interview\n\n" +
            "Good luck with your job search!"

    val drawerShouldBeOpened = MutableLiveData<Boolean>()
    val chatStatusLiveData = MutableLiveData<ChatStatus>().apply { value = ChatStatus.DEFAULT }

    //使用 shared flow 为了解决数据倒灌的问题....
    private val _loadVITSModelLiveData = MutableSharedFlow<VITSLoadStatus>()
    val loadVITSModelLiveData = _loadVITSModelLiveData.asSharedFlow()
    private val _chatContentUIFlow = MutableSharedFlow<ChatDialogContentUIState>()
    val chatContentUIFlow = _chatContentUIFlow.asSharedFlow()

    val generateSoundLiveData = MutableLiveData<Boolean>()
    val initModelResultLiveData = MutableLiveData<List<ChannelListBean>>()
    val loadingUILiveData = MutableLiveData<Pair<Boolean, String>>()

    var currentLive2DModelPath: String = ""
    var currentLive2DModelName: String = ""
    var currentVITSModelName: String = ""
    var needTranslate: Boolean = true
    var needChatGPTProxy: Boolean = false

    private val chatGPTNetService: ChatGPTNetService? by lazy {
        ChatGPTNetService(ChatWaifuApplication.context)
    }
    private val vitsHelper: SoundGenerateHelper by lazy {
        SoundGenerateHelper(ChatWaifuApplication.context)
    }
    private val localModelManager: LocalModelManager by lazy {
        LocalModelManager()
    }
    val lipsValueHandler: LipsValueHandler by lazy {
        LipsValueHandler()
    }
    private val sp: SharedPreferences by lazy {
        ChatWaifuApplication.context.getSharedPreferences(
            Constant.SAVED_STORE,
            Context.MODE_PRIVATE
        )
    }
    private val assistantMsgManager: AssistantMessageManager by lazy {
        AssistantMessageManager(ChatWaifuApplication.context)
    }
    private var translate: ITranslate? = null

    // Interview mode functions
    fun setInterviewMode(enabled: Boolean, docId: String? = null) {
        Log.d(TAG, "setInterviewMode called with enabled: $enabled, docId: $docId")
        isInterviewMode = enabled
        currentDocId = docId
        
        if (enabled) {
            currentInterviewQuestionIndex = 0
            interviewAnswers.clear()
            // Ensure we start with a clean state
            chatStatusLiveData.postValue(ChatStatus.INTERVIEW_MODE)
            Log.d(TAG, "Interview mode enabled, starting interview")
            // Start with first question
            startInterview()
        } else {
            chatStatusLiveData.postValue(ChatStatus.DEFAULT)
            Log.d(TAG, "Interview mode disabled")
        }
    }

    fun isInInterviewMode(): Boolean = isInterviewMode

    fun getCurrentInterviewQuestionIndex(): Int = currentInterviewQuestionIndex

    private fun startInterview() {
        Log.d(TAG, "startInterview called, currentIndex: $currentInterviewQuestionIndex, questions size: ${interviewQuestions.size}")
        if (currentInterviewQuestionIndex < interviewQuestions.size) {
            val question = interviewQuestions[currentInterviewQuestionIndex]
            Log.d(TAG, "Sending question: $question")
            sendInterviewQuestion(question)
        } else {
            Log.d(TAG, "No more questions to send")
        }
    }

    private fun sendInterviewQuestion(question: String) {
        Log.d(TAG, "sendInterviewQuestion called with: $question")
        CoroutineScope(Dispatchers.Main).launch {
            Log.d(TAG, "Emitting question to UI")
            _chatContentUIFlow.emit(
                ChatDialogContentUIState(
                    isFromMe = false,
                    chatContent = question
                )
            )
        }
        
        // In emulator, skip TTS completely
        if (isEmulator()) {
            Log.d(TAG, "Emulator detected, skipping TTS for interview question")
            return
        }
        
        // Generate and play TTS for the question
        Log.d(TAG, "Setting status to GENERATE_SOUND")
        chatStatusLiveData.postValue(ChatStatus.GENERATE_SOUND)
        Log.d(TAG, "Calling generateAndPlaySound")
        generateAndPlaySound(question)
    }

    fun handleInterviewResponse(userAnswer: String) {
        if (!isInterviewMode) return
        
        // Save user's answer
        interviewAnswers.add(userAnswer)
        
        // Move to next question or finish interview
        currentInterviewQuestionIndex++
        
        if (currentInterviewQuestionIndex < interviewQuestions.size) {
            // Send next question
            val nextQuestion = interviewQuestions[currentInterviewQuestionIndex]
            sendInterviewQuestion(nextQuestion)
        } else {
            // Interview completed, send tips
            finishInterview()
        }
    }

    private fun finishInterview() {
        Log.d(TAG, "finishInterview called")
        CoroutineScope(Dispatchers.Main).launch {
            Log.d(TAG, "Emitting tips to UI")
            _chatContentUIFlow.emit(
                ChatDialogContentUIState(
                    isFromMe = false,
                    chatContent = interviewTips
                )
            )
        }
        
        // In emulator, skip TTS completely
        if (isEmulator()) {
            Log.d(TAG, "Emulator detected, skipping TTS for interview tips")
            // Exit interview mode
            isInterviewMode = false
            chatStatusLiveData.postValue(ChatStatus.DEFAULT)
            return
        }
        
        // Generate and play TTS for tips
        Log.d(TAG, "Setting status to GENERATE_SOUND for tips")
        chatStatusLiveData.postValue(ChatStatus.GENERATE_SOUND)
        Log.d(TAG, "Calling generateAndPlaySound for tips")
        generateAndPlaySound(interviewTips)
        
        // Exit interview mode
        isInterviewMode = false
        chatStatusLiveData.postValue(ChatStatus.DEFAULT)
    }

    fun refreshAllKeys() {
        sp.getString(Constant.SAVED_CHAT_KEY, null)?.let {
            chatGPTNetService?.setPrivateKey(it)
        }
        val translateAppId = sp.getString(Constant.SAVED_TRANSLATE_APP_ID, null)
        val translateKey = sp.getString(Constant.SAVED_TRANSLATE_KEY, null)
        setBaiduTranslate(translateAppId ?: return, translateKey ?: return)
        needTranslate = sp.getBoolean(Constant.SAVED_USE_TRANSLATE, true)
        needChatGPTProxy = sp.getBoolean(Constant.SAVED_USE_CHATGPT_PROXY, false)
        val proxyUrl = if(needChatGPTProxy) sp.getString(Constant.SAVED_USE_CHATGPT_PROXY_URL, null) else null
        chatGPTNetService?.updateRetrofit(proxyUrl)
    }

    fun initModel(context: Context) {
        initModelResultLiveData.postValue(emptyList())
        loadingUILiveData.postValue(Pair(true, "Init Models...."))
        viewModelScope.launch(Dispatchers.IO) {
            val finalModelList = mutableListOf<ChannelListBean>()
            localModelManager.initInnerModel(context, finalModelList)
            localModelManager.initExternalModel(context, finalModelList)
            initModelResultLiveData.postValue(finalModelList)
            loadingUILiveData.postValue(Pair(false, ""))
        }
        lipsValueHandler.initLipSync()
    }

    fun loadVitsModel(basePath: String) {
        loadingUILiveData.postValue(Pair(true, "Load VITS Model...."))
        val rootFiles = localModelManager.getVITSModelFiles(basePath)
        viewModelScope.launch(Dispatchers.IO) {
            val configResult = suspendCancellableCoroutine<Boolean> {
                vitsHelper.loadConfigs(rootFiles?.find { it.name.endsWith("json") }?.absolutePath) { isSuccess ->
                    it.safeResume(isSuccess)
                }
            }

            val binResult = suspendCancellableCoroutine<Boolean> {
                vitsHelper.loadModel(rootFiles?.find { it.name.endsWith("bin") }?.absolutePath) { isSuccess ->
                    it.safeResume(isSuccess)
                }
            }
            _loadVITSModelLiveData.emit(if (binResult && configResult) VITSLoadStatus.STATE_SUCCESS else VITSLoadStatus.STATE_FAILED)
            loadingUILiveData.postValue(Pair(false, ""))
        }
    }

    fun loadChatListCache(characterName: String) {
        CoroutineScope(Dispatchers.IO).launch {
            assistantMsgManager.loadChatListCache(characterName)
        }
    }

    fun loadModelSystemSetting(modelName: String) {
        chatGPTNetService?.setSystemRole(
            localModelManager.getModelSystemSetting(modelName) ?: return
        )
    }

    private suspend fun sendChatGPTRequest(
        msg: String,
        assistantList: List<String>
    ): ChatGPTResponseData? {
        return suspendCancellableCoroutine {
            chatGPTNetService?.setAssistantList(assistantList)
            chatGPTNetService?.sendChatMessage(msg) { response ->
                it.safeResume(response)
            }
        }
    }

    private suspend fun fetchTranslateIfNeed(responseText: String?): String? {
        translate ?: return responseText
        responseText ?: return null
        if (!needTranslate) {
            return responseText
        }
        chatStatusLiveData.postValue(ChatStatus.GENERATE_SOUND)
        return suspendCancellableCoroutine {
            translate?.getTranslateResult(responseText) { result ->
                it.safeResume(result?.ifBlank { responseText } ?: responseText)
            }
        }
    }

    private fun generateAndPlaySound(needPlayText: String?) {
        Log.d(TAG, "generateAndPlaySound called with text: $needPlayText")
        Log.d(TAG, "Current chat status: ${chatStatusLiveData.value}")
        
        // Skip TTS in emulator environment
        if (isEmulator()) {
            Log.d(TAG, "Skipping TTS in emulator environment")
            if (chatStatusLiveData.value == ChatStatus.GENERATE_SOUND) {
                Log.d(TAG, "Setting status to DEFAULT in emulator")
                chatStatusLiveData.postValue(ChatStatus.DEFAULT)
            }
            return
        }
        
        Log.d(TAG, "Calling vitsHelper.generateAndPlay")
        vitsHelper.generateAndPlay(text = needPlayText,
            targetSpeakerId = localModelManager.getVITSSpeakerId(currentLive2DModelName),
            callback = { isSuccess ->
            Log.d(TAG, "generate sound callback: $isSuccess")
            if (chatStatusLiveData.value == ChatStatus.GENERATE_SOUND) {
                Log.d(TAG, "Setting status to DEFAULT after TTS")
                chatStatusLiveData.postValue(ChatStatus.DEFAULT)
            }},
            forwardResult = {
                Log.d(TAG, "TTS forwardResult received")
                lipsValueHandler.sendLipsValues(it)
            }
        )
    }

    private fun isEmulator(): Boolean {
        return (android.os.Build.FINGERPRINT.startsWith("generic")
                || android.os.Build.FINGERPRINT.startsWith("unknown")
                || android.os.Build.MODEL.contains("google_sdk")
                || android.os.Build.MODEL.contains("Emulator")
                || android.os.Build.MODEL.contains("Android SDK built for x86")
                || android.os.Build.MANUFACTURER.contains("Genymotion")
                || (android.os.Build.BRAND.startsWith("generic") && android.os.Build.DEVICE.startsWith("generic"))
                || "google_sdk" == android.os.Build.PRODUCT)
    }

    private fun constructUIStateFromResponse(response: ChatGPTResponseData?): ChatDialogContentUIState {

        if (!response?.errorMsg.isNullOrEmpty()) {
            return ChatDialogContentUIState(isFromMe = false, errorMsg = response?.errorMsg)
        }

        return ChatDialogContentUIState(
            isFromMe = false,
            chatContent = response?.choices?.firstOrNull()?.message?.content?.trim() ?: ""
        )
    }

    fun sendMineMsgUIState(content: String) {
        CoroutineScope(Dispatchers.Main).launch {
            _chatContentUIFlow.emit(
                ChatDialogContentUIState(
                    isFromMe = true,
                    chatContent = content
                )
            )
        }
        
        // Handle interview mode
        if (isInterviewMode) {
            handleInterviewResponse(content)
        }
    }

    override fun onCleared() {
        vitsHelper.clear()
        lipsValueHandler.shutDown()
        super.onCleared()
    }

    fun openDrawer() {
        drawerShouldBeOpened.value = true
    }

    fun resetOpenDrawerAction() {
        drawerShouldBeOpened.value = false
    }

    private fun setBaiduTranslate(appid: String, privateKey: String) {
        translate = BaiduTranslateService(
            ChatWaifuApplication.context,
            appid = appid,
            privateKey = privateKey
        )
    }
}

fun <T> CancellableContinuation<T>.safeResume(value: T) {
    if (this.isActive) {
        (this as? Continuation<T>)?.resume(value)
    }
}