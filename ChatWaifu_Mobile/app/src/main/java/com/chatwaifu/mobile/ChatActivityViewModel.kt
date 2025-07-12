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

    var currentLive2DModelPath: String = ""
    var currentLive2DModelName: String = ""
    var currentVITSModelName: String = ""
    var needTranslate: Boolean = true
    var needChatGPTProxy: Boolean = false

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
    private var translate: ITranslate? = null

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

    fun mainLoop() {
        viewModelScope.launch(Dispatchers.IO) {
            while (true) {
                chatStatusLiveData.postValue(ChatStatus.FETCH_INPUT)
                val input = fetchInput()
                assistantMsgManager.insertUserMessage(input)

//                chatStatusLiveData.postValue(ChatStatus.SEND_REQUEST)
//                val response = sendChatGPTRequest(input, assistantMsgManager.getSendAssistantList())
//                assistantMsgManager.insertGPTMessage(response)
//                Log.d(TAG, "get response $response")
//                _chatContentUIFlow.emit(constructUIStateFromResponse(response))
//
//                val responseText = response?.choices?.firstOrNull()?.message?.content
//                val translateText = fetchTranslateIfNeed(responseText)
//                Log.d(TAG, "translate result: $translateText")
                chatStatusLiveData.postValue(ChatStatus.GENERATE_SOUND)
                //generateAndPlaySound(translateText)
                generateAndPlaySound(input)
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

    private fun setBaiduTranslate(appid: String, privateKey: String) {
        translate = BaiduTranslateService(
            ChatWaifuApplication.context,
            appid = appid,
            privateKey = privateKey
        )
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

    private suspend fun fetchInput(): String {
        return suspendCancellableCoroutine {
            inputFunc = { input ->
                it.safeResume(input)
            }
        }
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
        chatStatusLiveData.postValue(ChatStatus.TRANSLATE)
        return suspendCancellableCoroutine {
            translate?.getTranslateResult(responseText) { result ->
                it.safeResume(result?.ifBlank { responseText } ?: responseText)
            }
        }
    }

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
}

fun <T> CancellableContinuation<T>.safeResume(value: T) {
    if (this.isActive) {
        (this as? Continuation<T>)?.resume(value)
    }
}