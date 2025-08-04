package com.chatwaifu.mobile.ui.keywords

import android.content.Intent
import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import androidx.activity.viewModels
import androidx.recyclerview.widget.LinearLayoutManager
import com.chatwaifu.mobile.ChatActivity
import com.chatwaifu.mobile.databinding.ActivityKeywordsBinding
import com.chatwaifu.mobile.ui.resume.UploadResumeActivity
import com.chatwaifu.mobile.ui.resume.ResumeIssuesActivity
import com.google.android.flexbox.FlexboxLayout
import android.widget.TextView
import android.view.ViewGroup
import android.view.LayoutInflater
import android.graphics.drawable.GradientDrawable
import android.graphics.Color
import android.util.Log
import android.view.View
import android.widget.ArrayAdapter
import com.google.android.material.snackbar.Snackbar
import com.chatwaifu.mobile.ui.techinterview.TechInterviewActivity
import com.chatwaifu.mobile.R

class KeywordsActivity : AppCompatActivity() {

    private lateinit var binding: ActivityKeywordsBinding
    private val viewModel: KeywordsViewModel by viewModels()
    private val TAG = "KeywordsActivity"

    private val jobTitles = arrayOf(
        "Software Engineer",
        "Frontend Developer",
        "Backend Developer",
        "Full Stack Developer",
        "Data Scientist",
        "Machine Learning Engineer",
        "DevOps Engineer",
        "QA Engineer",
        "Mobile Developer",
        "UI/UX Designer",
        "Product Manager"
    )

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityKeywordsBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setupJobDropdown()
        setupButtons()
        setupObservers()
        
        // 获取doc_id并加载关键词
        val docId = intent.getStringExtra("doc_id") ?: "mock-doc-id-12345"
        Log.d(TAG, "Loading keywords for doc_id: $docId")
        
        // 使用真正的API调用
        viewModel.loadKeywords(docId)
    }

    private fun setupJobDropdown() {
        val adapter = ArrayAdapter(
            this,
            android.R.layout.simple_dropdown_item_1line,
            jobTitles
        )
        binding.etJobTitle.setAdapter(adapter)

        // 点击时显示下拉框
        binding.etJobTitle.setOnClickListener {
            binding.etJobTitle.showDropDown()
        }

        // 获得焦点时显示下拉框
        binding.etJobTitle.setOnFocusChangeListener { _, hasFocus ->
            if (hasFocus) binding.etJobTitle.showDropDown()
        }
    }

    private fun validateInput(jobTitle: String): Boolean {
        return if (jobTitle.isEmpty()) {
            binding.jobInputLayout.error = "Please select a job title"
            false
        } else {
            binding.jobInputLayout.error = null
            true
        }
    }

    private fun setupButtons() {
        // 返回按钮回到 ResumeIssuesActivity
        binding.btnBack.setOnClickListener {
            startActivity(Intent(this, ResumeIssuesActivity::class.java).apply {
                flags = Intent.FLAG_ACTIVITY_CLEAR_TOP // 清除返回栈
            })
            finish()
        }

        // 下一步按钮
        binding.btnNext.setOnClickListener {
            val jobTitle = binding.etJobTitle.text.toString()
            if (!validateInput(jobTitle)) {
                return@setOnClickListener
            }
            
            val docId = intent.getStringExtra("doc_id") ?: "mock-doc-id-12345"
            
            // 显示保存中的状态
            binding.btnNext.isEnabled = false
            binding.btnNext.text = "Saving..."
            
            // 调用API保存目标职位
            viewModel.saveTargetJob(docId, jobTitle) { success ->
                runOnUiThread {
                    if (success) {
                        // 保存成功，跳转到下一个界面
                        val currentKeywords = viewModel.keywords.value ?: listOf("Java", "Kotlin", "Android", "REST API")
                        val intent = Intent(this, com.chatwaifu.mobile.ui.techinterview.TechInterviewActivity::class.java).apply {
                            putExtra("doc_id", docId)
                            putExtra("keywords", currentKeywords.toTypedArray())
                            putExtra("job_title", jobTitle)
                        }
                        startActivity(intent)
                    } else {
                        // 保存失败，恢复按钮状态
                        binding.btnNext.isEnabled = true
                        binding.btnNext.text = getString(R.string.next)
                        showSnackbar("Failed to save target job. Please try again.")
                    }
                }
            }
        }
    }
    
    private fun setupObservers() {
        // 观察ViewModel的结果
        viewModel.keywords.observe(this) { keywords ->
            Log.d(TAG, "Received keywords: ${keywords.size} items")
            displayKeywords(keywords)
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
                showSnackbar(error)
            }
        }
        
        viewModel.targetJobSaved.observe(this) { saved ->
            if (saved) {
                Log.d(TAG, "Target job saved successfully")
                // 可以在这里添加成功提示
            }
        }
    }
    
    private fun showLoadingState() {
        // 显示加载状态，可以在关键词区域显示进度条
        binding.flexKeywords.removeAllViews()
        val loadingText = TextView(this)
        loadingText.text = "Extracting keywords from your resume..."
        loadingText.setTextColor(resources.getColor(android.R.color.darker_gray, null))
        loadingText.textSize = 16f
        loadingText.gravity = android.view.Gravity.CENTER
        loadingText.setPadding(32, 32, 32, 32)
        binding.flexKeywords.addView(loadingText)
    }
    
    private fun hideLoadingState() {
        // 加载完成，关键词会通过displayKeywords方法显示
    }
    
    private fun displayKeywords(keywords: List<String>) {
        val flexboxLayout = binding.flexKeywords
        flexboxLayout.removeAllViews()
        
        for (kw in keywords) {
            val tv = TextView(this)
            tv.text = kw
            tv.setTextColor(Color.WHITE)
            tv.textSize = 15f
            tv.setPadding(32, 16, 32, 16)
            val bg = GradientDrawable()
            bg.cornerRadius = 48f
            bg.setColor(Color.parseColor("#3A5BA0")) // 比primary_blue_light深一点
            tv.background = bg
            val lp = ViewGroup.MarginLayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT)
            lp.setMargins(12, 12, 12, 12)
            tv.layoutParams = lp
            flexboxLayout.addView(tv)
        }
    }
    
    private fun showSnackbar(message: String) {
        Snackbar.make(binding.root, message, Snackbar.LENGTH_LONG).show()
    }
    
    // 测试方法：验证API连接
    private fun testApiConnection() {
        val docId = intent.getStringExtra("doc_id") ?: "mock-doc-id-12345"
        Log.d(TAG, "Testing API connection for doc_id: $docId")
        
        // 测试保存目标职位
        viewModel.saveTargetJob(docId, "Software Engineer") { success ->
            runOnUiThread {
                if (success) {
                    Log.d(TAG, "✅ API connection test successful")
                    showSnackbar("API connection test successful!")
                } else {
                    Log.e(TAG, "❌ API connection test failed")
                    showSnackbar("API connection test failed!")
                }
            }
        }
    }
}