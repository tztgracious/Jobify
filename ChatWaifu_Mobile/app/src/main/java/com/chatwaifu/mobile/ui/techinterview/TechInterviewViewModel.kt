package com.chatwaifu.mobile.ui.techinterview

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel

class TechInterviewViewModel : ViewModel() {
    
    private val _question = MutableLiveData<String>()
    val question: LiveData<String> = _question
    
    private val _isLoading = MutableLiveData<Boolean>()
    val isLoading: LiveData<Boolean> = _isLoading
    
    private val _error = MutableLiveData<String>()
    val error: LiveData<String> = _error
    
    fun loadTechQuestion(docId: String, jobTitle: String) {
        _isLoading.value = true
        _error.value = ""
        
        // TODO: 实现从后端API获取技术问题的逻辑
        // 这里暂时使用模拟数据
        val mockQuestions = mapOf(
            "Software Engineer" to "Please briefly explain how Retrofit works.",
            "Frontend Developer" to "Explain the difference between React and Vue.js.",
            "Backend Developer" to "Describe the benefits of using microservices architecture.",
            "Data Scientist" to "Explain the concept of overfitting in machine learning.",
            "DevOps Engineer" to "How would you implement CI/CD pipeline for a mobile app?"
        )
        
        val question = mockQuestions[jobTitle] ?: "Please briefly explain how Retrofit works."
        _question.value = question
        _isLoading.value = false
    }
    
    fun submitAnswer(answer: String) {
        // TODO: 实现提交答案到后端的逻辑
        // 这里可以添加网络请求来保存用户的答案
    }
} 