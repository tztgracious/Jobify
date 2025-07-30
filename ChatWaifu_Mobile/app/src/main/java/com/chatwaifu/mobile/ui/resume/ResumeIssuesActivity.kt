package com.chatwaifu.mobile.ui.resume

import android.content.Intent
import android.os.Bundle
import android.util.Log
import android.view.View
import androidx.appcompat.app.AppCompatActivity
import androidx.activity.viewModels
import androidx.recyclerview.widget.LinearLayoutManager
import com.chatwaifu.mobile.databinding.ActivityResumeIssuesBinding
import com.chatwaifu.mobile.ui.keywords.KeywordsActivity
import com.chatwaifu.mobile.ui.resume.UploadResumeActivity
import com.google.android.material.snackbar.Snackbar

class ResumeIssuesActivity : AppCompatActivity() {

    private lateinit var binding: ActivityResumeIssuesBinding
    private val viewModel: ResumeIssuesViewModel by viewModels()
    private lateinit var adapter: ResumeIssuesAdapter
    private val TAG = "ResumeIssuesActivity"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityResumeIssuesBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setupRecyclerView()
        setupButtons()
        setupObservers()

        // 获取doc_id并开始分析
        val docId = intent.getStringExtra("doc_id") ?: "mock-doc-id-12345"
        Log.d(TAG, "Starting resume analysis for doc_id: $docId")
        viewModel.analyzeResume(docId)
    }

    private fun setupRecyclerView() {
        adapter = ResumeIssuesAdapter()
        binding.rvIssues.apply {
            layoutManager = LinearLayoutManager(this@ResumeIssuesActivity)
            adapter = this@ResumeIssuesActivity.adapter
        }
    }

    private fun setupButtons() {
        binding.btnBack.setOnClickListener {
            Log.d(TAG, "Back button clicked.")
            // 返回到UploadResumeActivity
            startActivity(Intent(this, UploadResumeActivity::class.java).apply {
                flags = Intent.FLAG_ACTIVITY_CLEAR_TOP
            })
            finish()
        }

        binding.btnNext.setOnClickListener {
            Log.d(TAG, "Next button clicked.")
            
            // 调试：先测试API连接
            val docId = intent.getStringExtra("doc_id") ?: "mock-doc-id-12345"
            Log.d(TAG, "Testing API connection before proceeding...")
            viewModel.testApiConnection(docId)
            
            // 跳转到KeywordsActivity
            val keywords = intent.getStringArrayExtra("keywords") ?: arrayOf("Java", "Kotlin", "Android", "REST API")
            startActivity(Intent(this, KeywordsActivity::class.java).apply {
                putExtra("doc_id", docId)
                putExtra("keywords", keywords)
            })
        }
    }

    private fun setupObservers() {
        viewModel.issues.observe(this) { issues ->
            Log.d(TAG, "Received issues: ${issues.size} items")
            if (issues.isNotEmpty()) {
                // 验证问题数据是否包含有效内容
                val validIssues = issues.filter { issue ->
                    issue.title.isNotBlank() && 
                    issue.description.isNotBlank() &&
                    !issue.title.contains("{") && 
                    !issue.description.contains("{") &&
                    !issue.title.contains("[") && 
                    !issue.description.contains("[")
                }
                
                if (validIssues.isNotEmpty()) {
                    showIssuesList(validIssues)
                } else {
                    // 如果所有问题都无效，显示成功消息
                    showEmptyState()
                }
            } else {
                // 只有在没有收到任何issues时才显示空状态
                // 如果issues列表为空但ViewModel还在加载，则不显示空状态
                if (!viewModel.isLoading.value!!) {
                    showEmptyState()
                }
            }
        }

        viewModel.isLoading.observe(this) { isLoading ->
            Log.d(TAG, "Loading state changed: $isLoading")
            if (isLoading) {
                showLoadingState()
            } else {
                hideLoadingState()
            }
        }

        viewModel.error.observe(this) { error ->
            if (error.isNotEmpty()) {
                Log.d(TAG, "Showing error: $error")
                
                // 只有在没有有效数据时才显示错误
                val currentIssues = viewModel.issues.value
                if (currentIssues.isNullOrEmpty()) {
                    // 根据错误类型显示不同的消息
                    val userFriendlyError = when {
                        error.contains("Network error") -> "Connection issue. Please check your internet connection and try again."
                        error.contains("Analysis failed") -> "Resume analysis encountered an issue. Please try again."
                        error.contains("processing") -> "Resume is still being analyzed. Please wait a moment."
                        error.contains("longer than expected") -> "Analysis is taking longer than usual. Please try again in a few minutes."
                        else -> "An unexpected issue occurred. Please try again."
                    }
                    
                    showSnackbar(userFriendlyError)
                    viewModel.clearError()
                    
                    // 如果出现错误且没有数据，显示默认的成功消息
                    if (!viewModel.isLoading.value!!) {
                        showEmptyState()
                    }
                } else {
                    // 如果有有效数据，清除错误但不显示错误消息
                    viewModel.clearError()
                }
            }
        }
    }

    private fun showLoadingState() {
        binding.loadingLayout.visibility = View.VISIBLE
        binding.rvIssues.visibility = View.GONE
        binding.emptyLayout.visibility = View.GONE
    }

    private fun hideLoadingState() {
        binding.loadingLayout.visibility = View.GONE
    }

    private fun showIssuesList(issues: List<ResumeIssue>) {
        binding.rvIssues.visibility = View.VISIBLE
        binding.emptyLayout.visibility = View.GONE
        adapter.updateIssues(issues)
    }

    private fun showEmptyState() {
        binding.rvIssues.visibility = View.GONE
        binding.emptyLayout.visibility = View.VISIBLE
    }

    private fun showSnackbar(message: String) {
        Snackbar.make(binding.root, message, Snackbar.LENGTH_LONG).show()
        Log.d(TAG, "Showing Snackbar: $message")
    }
} 