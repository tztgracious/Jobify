package com.chatwaifu.mobile.ui.techinterview

import android.util.Log
import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.chatwaifu.mobile.data.network.JobifyApiService
import com.chatwaifu.mobile.data.network.QuestionsRequest
import com.chatwaifu.mobile.data.network.TechAnswerRequest
import kotlinx.coroutines.launch

class TechInterviewViewModel : ViewModel() {
    
    private val TAG = "TechInterviewViewModel"
    
    private val _question = MutableLiveData<String>()
    val question: LiveData<String> = _question
    
    private val _originalQuestion = MutableLiveData<String>() // 保存原始问题文本
    val originalQuestion: LiveData<String> = _originalQuestion
    
    private val _isLoading = MutableLiveData<Boolean>()
    val isLoading: LiveData<Boolean> = _isLoading
    
    private val _error = MutableLiveData<String>()
    val error: LiveData<String> = _error
    
    private val _answerSubmitted = MutableLiveData<Boolean>()
    val answerSubmitted: LiveData<Boolean> = _answerSubmitted
    
    private val apiService = JobifyApiService.create()
    
    fun loadTechQuestion(docId: String, jobTitle: String) {
        _isLoading.value = true
        _error.value = ""
        
        viewModelScope.launch {
            try {
                Log.d(TAG, "Loading tech questions for doc_id: $docId, job_title: $jobTitle")
                
                // 轮询等待问题生成完成
                var attempts = 0
                val maxAttempts = 10
                
                while (attempts < maxAttempts) {
                    attempts++
                    Log.d(TAG, "Attempt $attempts to load questions")
                    
                    val request = QuestionsRequest(id = docId)
                    Log.d(TAG, "API request: $request")
                    val response = apiService.getAllQuestions(request)
                    
                    if (response.isSuccessful) {
                        val questionsResponse = response.body()
                        Log.d(TAG, "Questions response: $questionsResponse")
                        Log.d(TAG, "Response finished: ${questionsResponse?.finished}")
                        Log.d(TAG, "Response tech_questions: ${questionsResponse?.tech_questions}")
                        
                        if (questionsResponse?.finished == true) {
                            val techQuestions = questionsResponse.tech_questions
                            Log.d(TAG, "Tech questions array: $techQuestions")
                            Log.d(TAG, "Tech questions array size: ${techQuestions.size}")
                            
                            if (techQuestions.isNotEmpty()) {
                                val firstTechQuestion = techQuestions[0] // 获取第一个技术问题
                                Log.d(TAG, "Raw tech question from API: '$firstTechQuestion'")
                                Log.d(TAG, "Question length: ${firstTechQuestion.length}")
                                Log.d(TAG, "Question bytes: ${firstTechQuestion.toByteArray().contentToString()}")
                                
                                // 直接使用原始问题文本，不进行任何处理
                                Log.d(TAG, "About to post question to LiveData: '$firstTechQuestion'")
                                _question.postValue(firstTechQuestion)
                                _originalQuestion.postValue(firstTechQuestion)
                                Log.d(TAG, "Posted question to LiveData: '$firstTechQuestion'")
                                Log.d(TAG, "Saved original question: '${_originalQuestion.value}'")
                                break // 成功获取问题，退出轮询
                            } else {
                                Log.w(TAG, "No tech questions available")
                                _error.postValue("No technical questions available")
                                break
                            }
                        } else {
                            Log.d(TAG, "Questions still being generated, waiting...")
                            if (attempts >= maxAttempts) {
                                Log.w(TAG, "Max attempts reached, questions not finished processing")
                                _error.postValue("Questions are still being generated. Please wait and try again.")
                                break
                            }
                            // 等待2秒后重试
                            kotlinx.coroutines.delay(2000)
                        }
                    } else {
                        val errorBody = response.errorBody()?.string()
                        Log.e(TAG, "Failed to load questions with status: ${response.code()}, error: $errorBody")
                        _error.postValue("Failed to load questions: ${response.code()} - $errorBody")
                        break
                    }
                }
                
            } catch (e: Exception) {
                Log.e(TAG, "Error loading tech questions", e)
                _error.postValue("Network error: ${e.message}")
            } finally {
                _isLoading.postValue(false)
            }
        }
    }
    
    fun submitAnswer(docId: String, question: String, answer: String, onComplete: (Boolean) -> Unit) {
        _isLoading.value = true
        _error.value = ""
        
        viewModelScope.launch {
            try {
                Log.d(TAG, "Submitting tech answer for doc_id: $docId")
                Log.d(TAG, "Question: '$question'")
                Log.d(TAG, "Answer: '$answer'")
                
                // 使用原始问题文本，确保完全匹配
                val originalQuestionText = _originalQuestion.value ?: question
                Log.d(TAG, "Using original question text: '$originalQuestionText'")
                Log.d(TAG, "Original question length: ${originalQuestionText.length}")
                Log.d(TAG, "Original question bytes: ${originalQuestionText.toByteArray().contentToString()}")
                
                val request = TechAnswerRequest(
                    id = docId,
                    index = 0, // 第一个技术问题
                    question = originalQuestionText,
                    answer = answer
                )
                
                Log.d(TAG, "API request: $request")
                Log.d(TAG, "Request question field: '${request.question}'")
                Log.d(TAG, "Request question length: ${request.question.length}")
                Log.d(TAG, "Request answer field: '${request.answer}'")
                Log.d(TAG, "Request id field: '${request.id}'")
                Log.d(TAG, "Request index field: ${request.index}")
                
                val response = apiService.submitTechAnswer(request)
                
                if (response.isSuccessful) {
                    val techAnswerResponse = response.body()
                    Log.d(TAG, "Tech answer submitted successfully: $techAnswerResponse")
                    _answerSubmitted.postValue(true)
                    onComplete(true)
                } else {
                    val errorBody = response.errorBody()?.string()
                    Log.e(TAG, "Failed to submit tech answer with status: ${response.code()}, error: $errorBody")
                    _error.postValue("Failed to submit answer: ${response.code()} - $errorBody")
                    _answerSubmitted.postValue(false)
                    onComplete(false)
                }
                
            } catch (e: Exception) {
                Log.e(TAG, "Error submitting tech answer", e)
                _error.postValue("Network error: ${e.message}")
                _answerSubmitted.postValue(false)
                onComplete(false)
            } finally {
                _isLoading.postValue(false)
            }
        }
    }
} 