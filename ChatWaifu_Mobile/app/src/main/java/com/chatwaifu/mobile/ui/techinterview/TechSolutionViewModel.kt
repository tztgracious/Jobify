package com.chatwaifu.mobile.ui.techinterview

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel

data class TechSolution(
    val standardAnswer: String
)

class TechSolutionViewModel : ViewModel() {
    
    private val _solution = MutableLiveData<TechSolution>()
    val solution: LiveData<TechSolution> = _solution
    
    private val _isLoading = MutableLiveData<Boolean>()
    val isLoading: LiveData<Boolean> = _isLoading
    
    private val _error = MutableLiveData<String>()
    val error: LiveData<String> = _error
    
    fun loadSolution(docId: String, jobTitle: String, question: String, userAnswer: String) {
        _isLoading.value = true
        _error.value = ""
        
        // TODO: 实现从后端API获取解决方案的逻辑
        // 这里暂时使用模拟数据
        val mockSolutions = mapOf(
            "Please briefly explain how Retrofit works." to TechSolution(
                standardAnswer = "Retrofit is a type-safe HTTP client for Android and Java developed by Square. It allows you to define your API interface as a Java interface and automatically generates the implementation for you. Key features include: 1) Type-safe API calls, 2) Automatic JSON parsing, 3) Support for various HTTP methods, 4) Request/response interceptors, 5) Easy integration with RxJava and other reactive libraries."
            ),
            "Explain the difference between React and Vue.js." to TechSolution(
                standardAnswer = "React and Vue.js are both popular JavaScript frameworks for building user interfaces. React uses JSX and a virtual DOM, while Vue uses templates and a reactive data system. React has a larger ecosystem and is backed by Facebook, while Vue is more lightweight and easier to learn for beginners."
            ),
            "Describe the benefits of using microservices architecture." to TechSolution(
                standardAnswer = "Microservices architecture offers several benefits: 1) Independent deployment and scaling, 2) Technology diversity, 3) Fault isolation, 4) Team autonomy, 5) Easier maintenance and updates. However, it also introduces complexity in service communication and data consistency."
            )
        )
        
        val solution = mockSolutions[question] ?: TechSolution(
            standardAnswer = "This is a comprehensive answer that covers all the key points. Consider providing specific examples and real-world applications to strengthen your response."
        )
        
        _solution.value = solution
        _isLoading.value = false
    }
    
    fun submitFeedback(feedback: String) {
        // TODO: 实现提交反馈到后端的逻辑
        // 这里可以添加网络请求来保存用户的反馈
    }
} 