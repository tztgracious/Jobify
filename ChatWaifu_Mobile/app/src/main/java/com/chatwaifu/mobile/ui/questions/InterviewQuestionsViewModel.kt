package com.chatwaifu.mobile.ui.questions

import android.util.Log
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.chatwaifu.mobile.data.network.JobifyApiService
import com.chatwaifu.mobile.data.network.QuestionsRequest
import com.chatwaifu.mobile.data.network.SubmitInterviewAnswerRequest
import kotlinx.coroutines.launch
import okhttp3.RequestBody
import okhttp3.MediaType.Companion.toMediaTypeOrNull

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
                Log.d(TAG, "Loading interview questions for docId: $docId")
                
                val request = QuestionsRequest(id = docId)
                val response = apiService.getAllQuestions(request)
                
                if (response.isSuccessful) {
                    val questionsResponse = response.body()
                    Log.d(TAG, "API Response: $questionsResponse")
                    
                    if (questionsResponse != null) {
                        if (questionsResponse.finished) {
                            // 合并技术问题和面试问题
                            val allQuestions = mutableListOf<String>()
                            
                            // 添加技术问题（如果有）
                            if (questionsResponse.tech_questions.isNotEmpty()) {
                                allQuestions.addAll(questionsResponse.tech_questions)
                            }
                            
                            // 添加面试问题
                            allQuestions.addAll(questionsResponse.interview_questions)
                            
                            Log.d(TAG, "Loaded ${allQuestions.size} questions (${questionsResponse.tech_questions.size} tech + ${questionsResponse.interview_questions.size} interview)")
                            questions.postValue(allQuestions)
                        } else {
                            error.postValue("questions_generating")
                            Log.d(TAG, "Questions not ready yet: ${questionsResponse.message}")
                        }
                    } else {
                        error.postValue("error_load_failed")
                        Log.e(TAG, "Response body is null")
                    }
                } else {
                    val errorBody = response.errorBody()?.string()
                    error.postValue("error_load_failed")
                    Log.e(TAG, "Failed to load questions: ${response.code()}, error: $errorBody")
                }
                
            } catch (e: Exception) {
                error.postValue("error_network")
                Log.e(TAG, "Error loading questions", e)
                Log.e(TAG, "Exception type: ${e.javaClass.simpleName}")
                Log.e(TAG, "Exception message: ${e.message}")
            } finally {
                isLoading.postValue(false)
            }
        }
    }
    
    fun submitAnswer(docId: String, questionIndex: Int, question: String, answer: String, answerType: String) {
        viewModelScope.launch {
            try {
                Log.d(TAG, "Submitting answer for question $questionIndex: $question")
                Log.d(TAG, "Answer: $answer")
                Log.d(TAG, "Answer type: $answerType")
                
                if (answerType == "text") {
                    // 文本答案使用JSON格式
                    val request = SubmitInterviewAnswerRequest(
                        id = docId,
                        index = questionIndex,
                        answer_type = answerType,
                        question = question,
                        answer = answer
                    )
                    
                    val response = apiService.submitInterviewAnswerText(request)
                    
                    if (response.isSuccessful) {
                        val submitResponse = response.body()
                        Log.d(TAG, "Text answer submitted successfully: $submitResponse")
                        Log.d(TAG, "Progress: ${submitResponse?.progress}%, Completed: ${submitResponse?.is_completed}")
                    } else {
                        val errorBody = response.errorBody()?.string()
                        Log.e(TAG, "Failed to submit text answer: ${response.code()}, error: $errorBody")
                    }
                } else if (answerType == "video") {
                    // 视频答案使用Multipart格式
                    val idBody = RequestBody.create("text/plain".toMediaTypeOrNull(), docId)
                    val indexBody = RequestBody.create("text/plain".toMediaTypeOrNull(), questionIndex.toString())
                    val answerTypeBody = RequestBody.create("text/plain".toMediaTypeOrNull(), answerType)
                    val questionBody = RequestBody.create("text/plain".toMediaTypeOrNull(), question)
                    
                    // 注意：视频文件需要从VideoAnswerActivity传递过来
                    // 这里暂时只记录日志
                    Log.d(TAG, "Video answer submission not implemented yet")
                }
                
            } catch (e: Exception) {
                Log.e(TAG, "Error submitting answer", e)
                Log.e(TAG, "Exception type: ${e.javaClass.simpleName}")
                Log.e(TAG, "Exception message: ${e.message}")
            }
        }
    }
} 