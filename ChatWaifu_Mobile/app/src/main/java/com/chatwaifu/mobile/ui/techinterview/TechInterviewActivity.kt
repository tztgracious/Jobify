package com.chatwaifu.mobile.ui.techinterview

import android.content.Intent
import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import androidx.activity.viewModels
import com.chatwaifu.mobile.R
import com.chatwaifu.mobile.databinding.ActivityTechInterviewBinding
import com.chatwaifu.mobile.ui.answermode.AnswerModeSelectActivity
import com.chatwaifu.mobile.ui.keywords.KeywordsActivity
import com.chatwaifu.mobile.ui.techinterview.TechSolutionActivity
import android.util.Log
import android.view.View
import com.google.android.material.snackbar.Snackbar

class TechInterviewActivity : AppCompatActivity() {

    private lateinit var binding: ActivityTechInterviewBinding
    private val viewModel: TechInterviewViewModel by viewModels()
    private val TAG = "TechInterviewActivity"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityTechInterviewBinding.inflate(layoutInflater)
        setContentView(binding.root)

        Log.d(TAG, "TechInterviewActivity onCreate started")
        setupButtons()
        setupObservers()
        loadQuestion()
        Log.d(TAG, "TechInterviewActivity onCreate completed")
    }

    private fun setupButtons() {
        // 返回按钮回到 KeywordsActivity
        binding.btnBack.setOnClickListener {
            val docId = intent.getStringExtra("doc_id") ?: "mock-doc-id-12345"
            val keywords = intent.getStringArrayExtra("keywords") ?: arrayOf("Java", "Kotlin", "Android", "REST API")
            val jobTitle = intent.getStringExtra("job_title") ?: "Software Engineer"
            
            val intent = Intent(this, KeywordsActivity::class.java).apply {
                putExtra("doc_id", docId)
                putExtra("keywords", keywords)
                putExtra("job_title", jobTitle)
                flags = Intent.FLAG_ACTIVITY_CLEAR_TOP // 清除返回栈
            }
            startActivity(intent)
            finish()
        }

        // 下一步按钮跳转到 TechSolutionActivity
        binding.btnNext.setOnClickListener {
            val answer = binding.etAnswer.text.toString().trim()
            if (!validateInput(answer)) {
                return@setOnClickListener
            }
            
            // 获取传递的参数
            val docId = intent.getStringExtra("doc_id") ?: "mock-doc-id-12345"
            val keywords = intent.getStringArrayExtra("keywords") ?: arrayOf("Java", "Kotlin", "Android", "REST API")
            val jobTitle = intent.getStringExtra("job_title") ?: "Software Engineer"
            val question = viewModel.originalQuestion.value ?: binding.tvQuestion.text.toString()
            
            // 显示提交中的状态
            binding.btnNext.isEnabled = false
            binding.btnNext.text = "Submitting..."
            
            // 调用API提交技术答案
            viewModel.submitAnswer(docId, question, answer) { success ->
                runOnUiThread {
                    if (success) {
                        // 提交成功，跳转到标准答案界面
                        val intent = Intent(this, TechSolutionActivity::class.java).apply {
                            putExtra("doc_id", docId)
                            putExtra("keywords", keywords)
                            putExtra("job_title", jobTitle)
                            putExtra("tech_question", question)
                            putExtra("tech_answer", answer)
                        }
                        startActivity(intent)
                    } else {
                        // 提交失败，恢复按钮状态
                        binding.btnNext.isEnabled = true
                        binding.btnNext.text = getString(R.string.next)
                        showSnackbar("Failed to submit answer. Please try again.")
                    }
                }
            }
        }
    }

    private fun validateInput(answer: String): Boolean {
        return if (answer.isEmpty()) {
            binding.answerInputLayout.error = getString(R.string.validation_answer_required)
            false
        } else {
            binding.answerInputLayout.error = null
            true
        }
    }

    private fun setupObservers() {
        Log.d(TAG, "Setting up observers")
        viewModel.question.observe(this) { question ->
            Log.d(TAG, "Question observer triggered with: '$question'")
            Log.d(TAG, "Current tvQuestion text before update: '${binding.tvQuestion.text}'")
            binding.tvQuestion.text = question
            Log.d(TAG, "Current tvQuestion text after update: '${binding.tvQuestion.text}'")
        }
        
        viewModel.isLoading.observe(this) { isLoading ->
            if (isLoading) {
                binding.btnNext.isEnabled = false
                binding.btnNext.text = "Loading..."
                // 可以添加进度条或其他加载指示器
            } else {
                binding.btnNext.isEnabled = true
                binding.btnNext.text = getString(R.string.next)
            }
        }
        
        viewModel.error.observe(this) { error ->
            if (error.isNotEmpty()) {
                showSnackbar(error)
            }
        }
        
        viewModel.answerSubmitted.observe(this) { submitted ->
            if (submitted) {
                Log.d(TAG, "Answer submitted successfully")
                // 可以在这里添加成功提示
            }
        }
    }
    
    private fun loadQuestion() {
        // 总是从API加载问题，因为问题是从后端动态生成的
        val docId = intent.getStringExtra("doc_id") ?: "mock-doc-id-12345"
        val jobTitle = intent.getStringExtra("job_title") ?: "Software Engineer"
        
        Log.d(TAG, "loadQuestion called with docId: $docId, jobTitle: $jobTitle")
        Log.d(TAG, "Current tvQuestion text: '${binding.tvQuestion.text}'")
        viewModel.loadTechQuestion(docId, jobTitle)
        Log.d(TAG, "loadTechQuestion called")
    }
    
    private fun showSnackbar(message: String) {
        Snackbar.make(binding.root, message, Snackbar.LENGTH_LONG).show()
    }
    
    // 测试方法：验证API连接
    private fun testApiConnection() {
        val docId = intent.getStringExtra("doc_id") ?: "mock-doc-id-12345"
        val jobTitle = intent.getStringExtra("job_title") ?: "Software Engineer"
        Log.d(TAG, "Testing API connection for doc_id: $docId, job_title: $jobTitle")
        
        viewModel.loadTechQuestion(docId, jobTitle)
    }
} 