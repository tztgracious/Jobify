package com.chatwaifu.mobile.ui.resume

import android.util.Log
import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.chatwaifu.mobile.data.network.GrammarRequest
import com.chatwaifu.mobile.data.network.JobifyApiService
import kotlinx.coroutines.launch

class ResumeIssuesViewModel : ViewModel() {

    private val TAG = "ResumeIssuesViewModel"
    private val apiService = JobifyApiService.create()

    private val _issues = MutableLiveData<List<ResumeIssue>>()
    val issues: LiveData<List<ResumeIssue>> = _issues

    private val _isLoading = MutableLiveData<Boolean>()
    val isLoading: LiveData<Boolean> = _isLoading

    private val _error = MutableLiveData<String>()
    val error: LiveData<String> = _error

    fun analyzeResume(docId: String) {
        viewModelScope.launch {
            _isLoading.value = true
            _error.value = ""
            
            try {
                Log.d(TAG, "Starting grammar analysis for doc_id: $docId")
                
                // 轮询检查处理状态，最多等待60秒
                var attempts = 0
                val maxAttempts = 12 // 12次 * 5秒 = 60秒
                
                while (attempts < maxAttempts) {
                    attempts++
                    Log.d(TAG, "Checking grammar results (attempt $attempts/$maxAttempts)")
                    
                    val request = GrammarRequest(id = docId)
                    val response = apiService.getGrammarResults(request)
                    
                    if (response.isSuccessful) {
                        val grammarResponse = response.body()
                        Log.d(TAG, "Grammar response (attempt $attempts): $grammarResponse")
                        
                        if (grammarResponse?.finished == true) {
                            val grammarCheck = grammarResponse.grammar_check
                            if (grammarCheck != null && grammarCheck.matches.isNotEmpty()) {
                                // 将语法检查结果转换为ResumeIssue格式
                                val issues = convertGrammarMatchesToIssues(grammarCheck.matches)
                                _issues.value = issues
                                Log.d(TAG, "Found ${issues.size} grammar issues")
                            } else {
                                // 没有语法问题，显示成功消息
                                _issues.value = listOf(
                                    ResumeIssue(
                                        title = "Resume Analysis Complete",
                                        description = "Great job! No grammar issues were found in your resume. Your resume looks well-written and professional.",
                                        type = ResumeIssue.Type.SUGGESTION
                                    )
                                )
                                Log.d(TAG, "No grammar issues found")
                            }
                            break // 处理完成，退出循环
                        } else {
                            // 还在处理中，等待5秒后重试
                            if (attempts < maxAttempts) {
                                Log.d(TAG, "Resume still processing, waiting 5 seconds... (attempt $attempts/$maxAttempts)")
                                // 更新加载状态，显示处理进度
                                _error.value = "Analyzing resume... Please wait (${attempts}/${maxAttempts})"
                                kotlinx.coroutines.delay(5000) // 等待5秒
                            } else {
                                _error.value = "Resume processing is taking longer than expected. Please try again later."
                            }
                        }
                    } else {
                        val errorBody = response.errorBody()?.string()
                        Log.e(TAG, "Grammar analysis failed with status: ${response.code()}, error: $errorBody")
                        _error.value = "Analysis failed: ${response.code()} - $errorBody"
                        break
                    }
                }
                
            } catch (e: Exception) {
                Log.e(TAG, "Error analyzing resume", e)
                _error.value = "Network error: ${e.message}"
            } finally {
                _isLoading.value = false
            }
        }
    }

    private fun convertGrammarMatchesToIssues(matches: List<com.chatwaifu.mobile.data.network.GrammarMatch>): List<ResumeIssue> {
        return matches.map { match ->
            ResumeIssue(
                title = match.shortMessage ?: match.message.take(50) + "...",
                description = "${match.message}\n\nContext: \"${match.context.text}\"\n\nSuggestion: ${match.replacements.firstOrNull()?.value ?: "Review this section"}",
                type = when (match.rule.category.id) {
                    "TYPOS" -> ResumeIssue.Type.CRITICAL
                    "GRAMMAR" -> ResumeIssue.Type.WARNING
                    else -> ResumeIssue.Type.SUGGESTION
                }
            )
        }
    }

    fun clearError() {
        _error.value = ""
    }
    
    // 调试方法：手动测试API连接
    fun testApiConnection(docId: String) {
        viewModelScope.launch {
            try {
                Log.d(TAG, "Testing API connection for doc_id: $docId")
                val request = GrammarRequest(id = docId)
                val response = apiService.getGrammarResults(request)
                
                Log.d(TAG, "Test response status: ${response.code()}")
                Log.d(TAG, "Test response body: ${response.body()}")
                
                if (response.isSuccessful) {
                    val grammarResponse = response.body()
                    Log.d(TAG, "Test - finished: ${grammarResponse?.finished}")
                    Log.d(TAG, "Test - grammar_check: ${grammarResponse?.grammar_check}")
                    Log.d(TAG, "Test - error: ${grammarResponse?.error}")
                } else {
                    val errorBody = response.errorBody()?.string()
                    Log.e(TAG, "Test failed: ${response.code()} - $errorBody")
                }
            } catch (e: Exception) {
                Log.e(TAG, "Test error", e)
            }
        }
    }
} 