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
import com.chatwaifu.mobile.data.network.JobifyApiService
import com.chatwaifu.mobile.data.network.QuestionsRequest
import com.chatwaifu.translate.ITranslate
import com.chatwaifu.translate.baidu.BaiduTranslateService
import com.chatwaifu.vits.utils.SoundGenerateHelper
import kotlinx.coroutines.CancellableContinuation
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.delay
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
    }

    enum class ChatStatus {
        DEFAULT,
        FETCH_INPUT,
        SEND_REQUEST,
        TRANSLATE,
        GENERATE_SOUND,
    }

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
    val isReady = MutableLiveData<Boolean>(false)

    var currentLive2DModelPath: String = ""
    var currentLive2DModelName: String = ""
    var currentVITSModelName: String = ""
    // var needTranslate: Boolean = true // 不再需要翻译
    var needChatGPTProxy: Boolean = false

    // 添加面试会话相关状态
    val sessionId = "interview_session_${System.currentTimeMillis()}"
    val currentQuestionText = MutableLiveData<String>()
    val currentQuestionIndexLiveData = MutableLiveData<Int>()
    
    // 答题模式管理
    private var answerMode: String = "text" // "text" or "video"
    val answerModeLiveData = MutableLiveData<String>()

    private var inputFunc: ((input: String) -> Unit)? = null
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
    // private var translate: ITranslate? = null // 不再需要翻译

    fun refreshAllKeys() {
        sp.getString(Constant.SAVED_CHAT_KEY, null)?.let {
            chatGPTNetService?.setPrivateKey(it)
        }
        // 不再需要翻译相关配置
        needChatGPTProxy = sp.getBoolean(Constant.SAVED_USE_CHATGPT_PROXY, false)
        val proxyUrl = if(needChatGPTProxy) sp.getString(Constant.SAVED_USE_CHATGPT_PROXY_URL, null) else null
        chatGPTNetService?.updateRetrofit(proxyUrl)
    }

    fun mainLoop() {
        viewModelScope.launch(Dispatchers.IO) {
            while (true) {
                chatStatusLiveData.postValue(ChatStatus.FETCH_INPUT)
                val input = fetchInput()
                assistantMsgManager.insertUserMessage(input)
                // sendMineMsgUIState(input) // 不再显示用户输入内容
                ////////////////////////////
                // 不再连接GPT，直接用模拟问题
                chatStatusLiveData.postValue(ChatStatus.SEND_REQUEST)
                val question = if (currentQuestionIndex < interviewQuestions.size) {
                    interviewQuestions[currentQuestionIndex]
                } else {
                    "Thank you for your answer. The interview is over."
                }
                
                // 更新当前问题状态
                currentQuestionText.postValue(question)
                currentQuestionIndexLiveData.postValue(currentQuestionIndex)
                
                // 构造模拟的回复UI
                val response = ChatGPTResponseData(
                    choices = listOf(
                        com.chatwaifu.chatgpt.ListBean(
                            message = com.chatwaifu.chatgpt.ResponseInnerMessageBean(
                                role = "assistant",
                                content = question
                            ),
                            index = 0,
                            finish_reason = null
                        )
                    ),
                    errorMsg = null
                )
                assistantMsgManager.insertGPTMessage(response)
                _chatContentUIFlow.emit(
                    constructUIStateFromResponse(response)
                )
                chatStatusLiveData.postValue(ChatStatus.GENERATE_SOUND)
                generateAndPlaySound(question)
                currentQuestionIndex += 1
            }
        }
    }

    fun sendMessage(input: String) {
        CoroutineScope(Dispatchers.IO).launch {
            if (inputFunc != null) {
                inputFunc?.invoke(input)
            }
        }
    }

    // private fun setBaiduTranslate(appid: String, privateKey: String) {
    //     translate = BaiduTranslateService(
    //         ChatWaifuApplication.context,
    //         appid = appid,
    //         privateKey = privateKey
    //     )
    // }


    fun initModel(context: Context) {
        initModelResultLiveData.postValue(emptyList())
        loadingUILiveData.postValue(Pair(true, "Init Models...."))
        viewModelScope.launch(Dispatchers.IO) {
            val finalModelList = mutableListOf<ChannelListBean>()
            localModelManager.initInnerModel(context, finalModelList)
            localModelManager.initExternalModel(context, finalModelList)
            // 自动选择 haru_greeter_t05
            val haru = finalModelList.find { it.characterName == "haru_greeter_t05" }
            if (haru != null) {
                currentLive2DModelName = haru.characterName
                currentLive2DModelPath = haru.characterPath
                currentVITSModelName = haru.characterName
                loadVitsModel(haru.characterVitsPath)
                loadChatListCache(haru.characterName)
                loadModelSystemSetting(haru.characterName)
            }
            // 不再通知UI显示角色列表
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

    private suspend fun fetchInput(): String {
        return suspendCancellableCoroutine {
            inputFunc = { input ->
                it.safeResume(input)
            }
        }
    }

    // private suspend fun sendChatGPTRequest(
    //     msg: String,
    //     assistantList: List<String>
    // ): ChatGPTResponseData? {
    //     return suspendCancellableCoroutine {
    //         chatGPTNetService?.setAssistantList(assistantList)
    //         chatGPTNetService?.sendChatMessage(msg) { response ->
    //             it.safeResume(response)
    //         }
    //     }
    // }

    // private suspend fun fetchTranslateIfNeed(responseText: String?): String? {
    //     translate ?: return responseText
    //     responseText ?: return null
    //     if (!needTranslate) {
    //         return responseText
    //     }
    //     chatStatusLiveData.postValue(ChatStatus.TRANSLATE)
    //     return suspendCancellableCoroutine {
    //         translate?.getTranslateResult(responseText) { result ->
    //             it.safeResume(result?.ifBlank { responseText } ?: responseText)
    //         }
    //     }
    // }

    private fun generateAndPlaySound(needPlayText: String?) {
        vitsHelper.generateAndPlay(text = needPlayText,
            targetSpeakerId = localModelManager.getVITSSpeakerId(currentLive2DModelName),
            callback = { isSuccess ->
            Log.d(TAG, "generate sound $isSuccess")
            if (chatStatusLiveData.value == ChatStatus.GENERATE_SOUND) {
                chatStatusLiveData.postValue(ChatStatus.DEFAULT)
            }},
            forwardResult = {
                lipsValueHandler.sendLipsValues(it)
            }
        )
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

    fun onReady() {
        isReady.postValue(true)
        // 检查问题是否已加载，如果没有则等待或使用默认问题
        viewModelScope.launch(Dispatchers.IO) {
            // 如果没有问题且没有docId，使用默认问题
            if (interviewQuestions.isEmpty() && docId == null) {
                setDefaultQuestions()
            }
            
            // 等待问题加载（最多等待5秒）
            var attempts = 0
            while (interviewQuestions.isEmpty() && attempts < 10) {
                Log.d(TAG, "Waiting for questions to load, attempt: ${attempts + 1}")
                kotlinx.coroutines.delay(500)
                attempts++
            }
            
            if (interviewQuestions.isEmpty()) {
                Log.w(TAG, "No questions loaded after waiting, using default questions")
                setDefaultQuestions()
            }
            
            val question = if (currentQuestionIndex < interviewQuestions.size) {
                interviewQuestions[currentQuestionIndex]
            } else {
                "Thank you for your answer. The interview is over."
            }
            
            Log.d(TAG, "Displaying question: $question")
            
            // 更新当前问题状态
            currentQuestionText.postValue(question)
            currentQuestionIndexLiveData.postValue(currentQuestionIndex)
            
            val response = com.chatwaifu.chatgpt.ChatGPTResponseData(
                choices = listOf(
                    com.chatwaifu.chatgpt.ListBean(
                        message = com.chatwaifu.chatgpt.ResponseInnerMessageBean(
                            role = "assistant",
                            content = question
                        ),
                        index = 0,
                        finish_reason = null
                    )
                ),
                errorMsg = null
            )
            assistantMsgManager.insertGPTMessage(response)
            _chatContentUIFlow.emit(
                constructUIStateFromResponse(response)
            )
            chatStatusLiveData.postValue(ChatStatus.GENERATE_SOUND)
            generateAndPlaySound(question)
            currentQuestionIndex = 1
        }
    }

    fun setAnswerMode(mode: String) {
        answerMode = mode
        answerModeLiveData.postValue(mode)
        Log.d(TAG, "Answer mode set to: $mode")
    }

    fun getAnswerMode(): String {
        return answerMode
    }

    // 获取当前会话信息
    fun getCurrentSessionInfo(): Triple<String, Int, String> {
        return Triple(
            sessionId,
            currentQuestionIndexLiveData.value ?: 0,
            currentQuestionText.value ?: "请回答这个问题"
        )
    }

    // Dynamic interview questions from backend
    private val interviewQuestions = mutableListOf<String>()
    private var currentQuestionIndex = 0
    private var docId: String? = null
    
    // Expose questions for UI
    private val _interviewQuestionsLiveData = MutableLiveData<List<String>>()
    val interviewQuestionsLiveData: MutableLiveData<List<String>> = _interviewQuestionsLiveData
    
    // Expose doc_id for UI
    private val _docIdLiveData = MutableLiveData<String?>()
    val docIdLiveData: MutableLiveData<String?> = _docIdLiveData
    
    fun setDocId(id: String) {
        docId = id
        _docIdLiveData.postValue(id)
        loadQuestionsFromBackend()
    }
    
    private fun loadQuestionsFromBackend() {
        docId?.let { id ->
            viewModelScope.launch(Dispatchers.IO) {
                val maxRetries = 10  // 最多重试10次
                val retryDelay = 3000L  // 每次重试间隔3秒
                
                for (attempt in 1..maxRetries) {
                    try {
                        Log.d(TAG, "Loading questions from backend for doc_id: $id (Attempt $attempt/$maxRetries)")
                        val apiService = JobifyApiService.create()
                        val request = QuestionsRequest(id = id)
                        val response = apiService.getAllQuestions(request)
                        
                        if (response.isSuccessful) {
                            val questionsResponse = response.body()
                            Log.d(TAG, "API Response: $questionsResponse")
                            
                            if (questionsResponse?.finished == true) {
                                // 只使用面试问题，不包含技术问题（技术问题由TechInterviewActivity单独处理）
                                val interviewQuestionsOnly = questionsResponse.interview_questions
                                Log.d(TAG, "Added ${interviewQuestionsOnly.size} interview questions (excluding tech questions)")
                                
                                interviewQuestions.clear()
                                interviewQuestions.addAll(interviewQuestionsOnly)
                                currentQuestionIndex = 0
                                
                                // Update LiveData for UI
                                _interviewQuestionsLiveData.postValue(interviewQuestions.toList())
                                
                                Log.d(TAG, "Successfully loaded ${interviewQuestions.size} interview questions from backend")
                                Log.d(TAG, "Questions: $interviewQuestions")
                                return@launch  // 成功加载，退出重试循环
                            } else {
                                Log.w(TAG, "Questions not finished yet (Attempt $attempt/$maxRetries), waiting...")
                                if (attempt < maxRetries) {
                                    delay(retryDelay)  // 等待3秒后重试
                                } else {
                                    Log.w(TAG, "Questions generation timeout after $maxRetries attempts, using default questions")
                                    setDefaultQuestions()
                                }
                            }
                        } else {
                            Log.e(TAG, "API call failed with status: ${response.code()}")
                            if (attempt >= maxRetries) {
                                setDefaultQuestions()
                            }
                        }
                    } catch (e: Exception) {
                        Log.e(TAG, "Error loading questions from backend (Attempt $attempt/$maxRetries)", e)
                        if (attempt >= maxRetries) {
                            setDefaultQuestions()
                        }
                    }
                }
            }
        } ?: run {
            Log.w(TAG, "No doc_id provided, using default questions")
            setDefaultQuestions()
        }
    }
    
    private fun setDefaultQuestions() {
        interviewQuestions.clear()
        interviewQuestions.addAll(listOf(
            "Please introduce yourself and tell me about your background.",
            "What are your greatest strengths and how would they benefit this role?",
            "Describe a challenging project you worked on and how you overcame obstacles."
        ))
        // Update LiveData for UI
        _interviewQuestionsLiveData.postValue(interviewQuestions.toList())
        Log.d(TAG, "Set default questions: ${interviewQuestions.size}")
    }
}

fun <T> CancellableContinuation<T>.safeResume(value: T) {
    if (this.isActive) {
        (this as? Continuation<T>)?.resume(value)
    }
}