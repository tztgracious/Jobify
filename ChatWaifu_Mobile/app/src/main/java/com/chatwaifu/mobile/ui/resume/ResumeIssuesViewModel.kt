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
                                
                                // 检查是否有有效的问题
                                if (issues.isNotEmpty()) {
                                    _issues.value = issues
                                    Log.d(TAG, "Found ${issues.size} grammar issues")
                                } else {
                                    // 如果没有有效的问题，显示成功消息
                                    _issues.value = listOf(
                                        ResumeIssue(
                                            title = "Resume Analysis Complete",
                                            description = "Excellent! Your resume has been analyzed and no grammar or spelling issues were found. Your writing is clear and professional. Keep up the good work!",
                                            type = ResumeIssue.Type.SUGGESTION
                                        )
                                    )
                                    Log.d(TAG, "No valid grammar issues found")
                                }
                            } else {
                                // 没有语法问题，显示成功消息
                                _issues.value = listOf(
                                    ResumeIssue(
                                        title = "Resume Analysis Complete",
                                        description = "Great job! Your resume has been thoroughly analyzed and no grammar or spelling issues were detected. Your resume appears to be well-written and professional.",
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
                                // 不设置错误消息，因为这是正常的处理过程
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
        return matches.mapNotNull { match ->
            try {
                // 清理和验证数据
                val cleanMessage = cleanText(match.message)
                val cleanShortMessage = match.shortMessage?.let { cleanText(it) }
                val cleanContextText = cleanText(match.context.text)
                val cleanSuggestion = match.replacements.firstOrNull()?.value?.let { cleanText(it) }
                
                // 如果清理后的消息为空，跳过这个匹配项
                if (cleanMessage.isBlank()) {
                    return@mapNotNull null
                }
                
                // 生成用户友好的标题
                val userFriendlyTitle = generateUserFriendlyTitle(cleanShortMessage, cleanMessage)
                
                // 生成格式化的描述
                val formattedDescription = formatDescription(cleanMessage, cleanContextText, cleanSuggestion)
                
                ResumeIssue(
                    title = userFriendlyTitle,
                    description = formattedDescription,
                    type = when (match.rule.category.id) {
                        "TYPOS" -> ResumeIssue.Type.CRITICAL
                        "GRAMMAR" -> ResumeIssue.Type.WARNING
                        else -> ResumeIssue.Type.SUGGESTION
                    }
                )
            } catch (e: Exception) {
                Log.e(TAG, "Error processing grammar match: $match", e)
                null // 跳过有问题的匹配项
            }
        }
    }
    
    /**
     * 生成用户友好的标题
     */
    private fun generateUserFriendlyTitle(shortMessage: String?, fullMessage: String): String {
        val baseTitle = shortMessage ?: fullMessage.take(60)
        
        return when {
            baseTitle.contains("grammar", ignoreCase = true) -> "Grammar Issue"
            baseTitle.contains("spell", ignoreCase = true) -> "Spelling Error"
            baseTitle.contains("punctuation", ignoreCase = true) -> "Punctuation Issue"
            baseTitle.contains("capitalization", ignoreCase = true) -> "Capitalization Issue"
            baseTitle.contains("word", ignoreCase = true) -> "Word Choice Issue"
            baseTitle.contains("sentence", ignoreCase = true) -> "Sentence Structure Issue"
            baseTitle.contains("verb", ignoreCase = true) -> "Verb Tense Issue"
            baseTitle.contains("article", ignoreCase = true) -> "Article Usage Issue"
            baseTitle.contains("preposition", ignoreCase = true) -> "Preposition Usage Issue"
            else -> baseTitle.capitalize()
        }
    }
    
    /**
     * 格式化描述文本，使其更易读
     */
    private fun formatDescription(message: String, context: String, suggestion: String?): String {
        return buildString {
            // 主要问题描述
            append(formatMessage(message))
            
            // 添加上下文（如果存在且有意义）
            if (context.isNotBlank() && context != message) {
                append("\n\nContext: \"$context\"")
            }
            
            // 添加建议（如果存在）
            if (suggestion != null && suggestion.isNotBlank() && suggestion != message) {
                append("\n\nSuggestion: $suggestion")
            }
        }
    }
    
    /**
     * 格式化消息文本，使其更易读
     */
    private fun formatMessage(message: String): String {
        return message
            .replace(Regex("\\s+"), " ") // 合并多个空格
            .replace(Regex("([.!?])\\s*([A-Z])"), "$1 $2") // 确保句子间有空格
            .replace(Regex("\\s+"), " ") // 再次合并空格
            .trim()
    }
    
    /**
     * 清理文本，去除JSON格式和特殊字符，并提高可读性
     */
    private fun cleanText(text: String): String {
        if (text.isBlank()) return ""
        
        return text.trim()
            .replace(Regex("\\{[^}]*\\}"), "") // 移除JSON对象
            .replace(Regex("\\[[^\\]]*\\]"), "") // 移除JSON数组
            .replace(Regex("\"[^\"]*\""), "") // 移除JSON字符串
            .replace(Regex("null"), "") // 移除null值
            .replace(Regex("\\s+"), " ") // 合并多个空格
            .replace(Regex("^[\\s,]+"), "") // 移除开头的空格和逗号
            .replace(Regex("[\\s,]+$"), "") // 移除结尾的空格和逗号
            .replace(Regex("_+"), " ") // 将下划线替换为空格
            .replace(Regex("\\|+"), " ") // 将竖线替换为空格
            .replace(Regex("\\\\+"), " ") // 将反斜杠替换为空格
            .replace(Regex("\\s+"), " ") // 再次合并空格
            .trim()
            .let { cleaned ->
                // 如果清理后只剩下标点符号或特殊字符，返回空字符串
                if (cleaned.matches(Regex("^[\\s\\p{Punct}]*$"))) {
                    ""
                } else {
                    cleaned
                }
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