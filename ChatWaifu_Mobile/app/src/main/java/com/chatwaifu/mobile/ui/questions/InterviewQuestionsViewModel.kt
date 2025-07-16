package com.chatwaifu.mobile.ui.questions

import android.util.Log
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.chatwaifu.mobile.data.network.JobifyApiService
import com.chatwaifu.mobile.data.network.QuestionsRequest
import kotlinx.coroutines.launch

class InterviewQuestionsViewModel : ViewModel() {
    
    private val TAG = "InterviewQuestionsViewModel"
    
    val questions = MutableLiveData<List<String>>()
    val isLoading = MutableLiveData<Boolean>()
    val error = MutableLiveData<String>()
    
    private val apiService = JobifyApiService.create()
    
    fun loadInterviewQuestions(docId: String) {
        isLoading.value = true
        error.value = ""
        
        viewModelScope.launch {
            try {
                // TODO: 实现真正的API调用
                /*
                val request = QuestionsRequest(doc_id = docId)
                val response = apiService.getInterviewQuestions(request)
                
                if (response.isSuccessful) {
                    val questionsResponse = response.body()
                    if (questionsResponse?.finished == true) {
                        questions.postValue(questionsResponse.questions)
                        Log.d(TAG, "Loaded ${questionsResponse.questions.size} questions")
                    } else {
                        error.postValue("questions_generating")
                        Log.d(TAG, "Questions not ready yet")
                    }
                } else {
                    error.postValue("error_load_failed")
                    Log.e(TAG, "Failed to load questions: ${response.code()}")
                }
                */
                
                // 模拟API调用 - 暂时使用模拟数据
                Log.d(TAG, "Using mock data for interview questions, docId: $docId")
                kotlinx.coroutines.delay(1500) // 模拟网络延迟
                
                // 模拟不同的面试问题
                val mockQuestions = when (docId) {
                    "mock-doc-id-12345" -> listOf(
                        "Please introduce yourself and tell me about your background.",
                        "What are your greatest strengths and how would they benefit this role?",
                        "Describe a challenging project you worked on and how you overcame obstacles."
                    )
                    "mock-doc-id-67890" -> listOf(
                        "Tell me about your experience with machine learning projects.",
                        "How do you stay updated with the latest AI technologies?",
                        "Describe a time when you had to explain complex technical concepts to non-technical stakeholders."
                    )
                    else -> listOf(
                        "What interests you about this position?",
                        "Where do you see yourself in 5 years?",
                        "What is your greatest professional achievement?"
                    )
                }
                
                questions.postValue(mockQuestions)
                Log.d(TAG, "Loaded ${mockQuestions.size} mock questions")
                
            } catch (e: Exception) {
                error.postValue("error_network")
                Log.e(TAG, "Error loading questions", e)
            } finally {
                isLoading.postValue(false)
            }
        }
    }
} 