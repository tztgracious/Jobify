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
            // 跳转到KeywordsActivity
            val docId = intent.getStringExtra("doc_id") ?: "mock-doc-id-12345"
            val keywords = intent.getStringArrayExtra("keywords") ?: arrayOf("Java", "Kotlin", "Android", "REST API")
            startActivity(Intent(this, KeywordsActivity::class.java).apply {
                putExtra("doc_id", docId)
                putExtra("keywords", keywords)
            })
        }
    }

    private fun setupObservers() {
        viewModel.issues.observe(this) { issues ->
            if (issues.isEmpty()) {
                showEmptyState()
            } else {
                showIssuesList(issues)
            }
        }

        viewModel.isLoading.observe(this) { isLoading ->
            if (isLoading) {
                showLoadingState()
            } else {
                hideLoadingState()
            }
        }

        viewModel.error.observe(this) { error ->
            if (error.isNotEmpty()) {
                showSnackbar(error)
                viewModel.clearError()
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