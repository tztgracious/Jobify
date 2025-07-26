package com.chatwaifu.mobile.ui.resume

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

class ResumeIssuesViewModel : ViewModel() {

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
                // 模拟API调用延迟
                delay(2000)
                
                // TODO: 这里应该调用真正的API来分析简历
                // 目前使用模拟数据
                val mockIssues = generateMockIssues()
                _issues.value = mockIssues
                
            } catch (e: Exception) {
                _error.value = "Error analyzing resume: ${e.message}"
            } finally {
                _isLoading.value = false
            }
        }
    }

    private fun generateMockIssues(): List<ResumeIssue> {
        return listOf(
            ResumeIssue(
                title = "Missing Contact Information",
                description = "Your resume should include a phone number and email address for potential employers to contact you.",
                type = ResumeIssue.Type.CRITICAL
            ),
            ResumeIssue(
                title = "Work Experience Descriptions Not Specific Enough",
                description = "Consider using specific numbers and achievements when describing work experience, such as 'increased efficiency by 30%' instead of 'improved efficiency'.",
                type = ResumeIssue.Type.WARNING
            ),
            ResumeIssue(
                title = "Skills Section Could Be More Detailed",
                description = "Consider adding skill proficiency levels (Beginner, Intermediate, Advanced) or relevant certifications.",
                type = ResumeIssue.Type.SUGGESTION
            ),
            ResumeIssue(
                title = "Incomplete Education Information",
                description = "Consider adding graduation year, GPA (if excellent), and relevant coursework information.",
                type = ResumeIssue.Type.WARNING
            ),
            ResumeIssue(
                title = "Consider Adding Project Experience",
                description = "If you have relevant project experience, consider adding a separate projects section to showcase your practical application skills.",
                type = ResumeIssue.Type.SUGGESTION
            ),
            ResumeIssue(
                title = "Resume Length Recommendation",
                description = "For experienced candidates, consider keeping your resume to 1-2 pages to ensure information is concise and clear.",
                type = ResumeIssue.Type.SUGGESTION
            )
        )
    }

    fun clearError() {
        _error.value = ""
    }
} 