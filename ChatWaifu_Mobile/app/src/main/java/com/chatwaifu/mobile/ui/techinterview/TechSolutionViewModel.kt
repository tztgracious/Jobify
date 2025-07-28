package com.chatwaifu.mobile.ui.techinterview

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.chatwaifu.mobile.data.network.JobifyApiService
import kotlinx.coroutines.launch
import android.util.Log

data class TechSolution(
    val standardAnswer: String
)

class TechSolutionViewModel : ViewModel() {
    
    private val apiService = JobifyApiService.createGraphRAG()
    private val TAG = "TechSolutionViewModel"
    
    private val _solution = MutableLiveData<TechSolution>()
    val solution: LiveData<TechSolution> = _solution
    
    private val _isLoading = MutableLiveData<Boolean>()
    val isLoading: LiveData<Boolean> = _isLoading
    
    private val _error = MutableLiveData<String>()
    val error: LiveData<String> = _error
    
    fun loadSolution(docId: String, jobTitle: String, question: String, userAnswer: String) {
        _isLoading.value = true
        _error.value = ""
        
        Log.d(TAG, "Starting GraphRAG solution load for question: '$question'")
        
        viewModelScope.launch {
            var attempts = 0
            val maxAttempts = 3  // 减少到3次重试，因为现在使用正确的API
            
            while (attempts < maxAttempts) {
                attempts++
                try {
                    Log.d(TAG, "Loading GraphRAG solution for question: '$question' (attempt $attempts)")
                    
                    // 使用GraphRAG API搜索标准答案
                    val response = apiService.searchLocal(question)
                    
                    if (response.isSuccessful) {
                        val graphRAGResponse = response.body()
                        Log.d(TAG, "GraphRAG response: $graphRAGResponse")
                        
                        if (graphRAGResponse != null) {
                            val standardAnswer = graphRAGResponse.response
                            Log.d(TAG, "Standard answer: '$standardAnswer'")
                            
                            val solution = TechSolution(standardAnswer = standardAnswer)
                            _solution.postValue(solution)
                            break // 成功获取答案，退出重试循环
                        } else {
                            Log.w(TAG, "GraphRAG response is null")
                            if (attempts >= maxAttempts) {
                                _error.postValue("Failed to get standard answer: Empty response")
                            }
                        }
                    } else {
                        val errorBody = response.errorBody()?.string()
                        Log.e(TAG, "Failed to get GraphRAG response with status: ${response.code()}, error: $errorBody")
                        if (attempts >= maxAttempts) {
                            _error.postValue("Failed to get standard answer: ${response.code()} - $errorBody")
                        }
                    }
                    
                } catch (e: Exception) {
                    Log.e(TAG, "Error loading GraphRAG solution (attempt $attempts)", e)
                    if (attempts >= maxAttempts) {
                        _error.postValue("Network error: ${e.message}")
                        
                        // 使用默认答案作为回退
                        val defaultAnswer = getDefaultAnswer(question)
                        val solution = TechSolution(standardAnswer = defaultAnswer)
                        _solution.postValue(solution)
                    } else {
                        // 等待一段时间后重试，延迟时间递增
                        val delayTime = (2000L * attempts)  // 2秒、4秒
                        Log.d(TAG, "Retrying in ${delayTime}ms...")
                        kotlinx.coroutines.delay(delayTime)
                    }
                }
            }
            
            _isLoading.postValue(false)
        }
    }
    
    private fun getDefaultAnswer(question: String): String {
        // 基于问题内容提供默认答案
        return when {
            question.contains("Retrofit", ignoreCase = true) -> {
                "Retrofit is a type-safe HTTP client for Android and Java developed by Square. It allows you to define your API interface as a Java interface and automatically generates the implementation for you. Key features include: 1) Type-safe API calls, 2) Automatic JSON parsing, 3) Support for various HTTP methods, 4) Request/response interceptors, 5) Easy integration with RxJava and other reactive libraries."
            }
            question.contains("React", ignoreCase = true) || question.contains("Vue", ignoreCase = true) -> {
                "React and Vue.js are both popular JavaScript frameworks for building user interfaces. React uses JSX and a virtual DOM, while Vue uses templates and a reactive data system. React has a larger ecosystem and is backed by Facebook, while Vue is more lightweight and easier to learn for beginners."
            }
            question.contains("microservices", ignoreCase = true) -> {
                "Microservices architecture offers several benefits: 1) Independent deployment and scaling, 2) Technology diversity, 3) Fault isolation, 4) Team autonomy, 5) Easier maintenance and updates. However, it also introduces complexity in service communication and data consistency."
            }
            question.contains("web application", ignoreCase = true) -> {
                "When designing a web application from scratch, consider: 1) Architecture patterns (MVC, MVVM), 2) Frontend framework selection (React, Vue, Angular), 3) Backend technology stack (Node.js, Python, Java), 4) Database design and optimization, 5) API design and documentation, 6) Security implementation, 7) Testing strategy, 8) Deployment and CI/CD pipeline."
            }
            question.contains("responsive", ignoreCase = true) || question.contains("interface", ignoreCase = true) -> {
                "For responsive and interactive user interfaces, consider: 1) Mobile-first design approach, 2) CSS Grid and Flexbox for layouts, 3) Progressive Web App (PWA) features, 4) Touch-friendly interface elements, 5) Performance optimization (lazy loading, code splitting), 6) Accessibility compliance, 7) Cross-browser compatibility, 8) Real-time updates and state management."
            }
            else -> {
                "This is a comprehensive answer that covers all the key points. Consider providing specific examples and real-world applications to strengthen your response. Focus on demonstrating your technical knowledge, problem-solving skills, and practical experience."
            }
        }
    }
    
    fun submitFeedback(feedback: String) {
        // TODO: 实现提交反馈到后端的逻辑
        // 这里可以添加网络请求来保存用户的反馈
    }
} 