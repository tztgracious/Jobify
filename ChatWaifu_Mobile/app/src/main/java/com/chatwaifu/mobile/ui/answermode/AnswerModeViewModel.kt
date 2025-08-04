package com.chatwaifu.mobile.ui.answermode

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel

data class AnswerMode(
    val mode: String,
    val title: String,
    val description: String,
    val icon: String
)

class AnswerModeViewModel : ViewModel() {
    
    private val _answerModes = MutableLiveData<List<AnswerMode>>()
    val answerModes: LiveData<List<AnswerMode>> = _answerModes
    
    private val _selectedMode = MutableLiveData<String>()
    val selectedMode: LiveData<String> = _selectedMode
    
    private val _isLoading = MutableLiveData<Boolean>()
    val isLoading: LiveData<Boolean> = _isLoading
    
    private val _error = MutableLiveData<String>()
    val error: LiveData<String> = _error
    
    init {
        loadAnswerModes()
    }
    
    fun loadAnswerModes() {
        _isLoading.value = true
        _error.value = ""
        
        // 模拟数据加载
        val modes = listOf(
            AnswerMode(
                mode = "text",
                title = "Text Answer",
                description = "Answer questions by typing text responses",
                icon = "edit"
            ),
            AnswerMode(
                mode = "video",
                title = "Video Answer", 
                description = "Record video responses to interview questions",
                icon = "videocam"
            )
        )
        
        _answerModes.value = modes
        _isLoading.value = false
    }
    
    fun selectMode(mode: String) {
        _selectedMode.value = mode
    }
    
    fun getModeInfo(mode: String): AnswerMode? {
        return _answerModes.value?.find { it.mode == mode }
    }
    
    fun validateSelection(): Boolean {
        return _selectedMode.value != null
    }
    
    fun submitSelection() {
        // TODO: 实现提交选择到后端的逻辑
        // 这里可以添加网络请求来保存用户的选择
        val selectedMode = _selectedMode.value
        if (selectedMode != null) {
            // 处理选择逻辑
        }
    }
} 