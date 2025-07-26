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

        setupButtons()
        setupObservers()
        loadQuestion()
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
            val question = binding.tvQuestion.text.toString()
            
            // 跳转到 TechSolutionActivity
            val intent = Intent(this, TechSolutionActivity::class.java).apply {
                putExtra("doc_id", docId)
                putExtra("keywords", keywords)
                putExtra("job_title", jobTitle)
                putExtra("tech_question", question)
                putExtra("tech_answer", answer)
            }
            startActivity(intent)
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
        viewModel.question.observe(this) { question ->
            binding.tvQuestion.text = question
        }
        
        viewModel.isLoading.observe(this) { isLoading ->
            // TODO: 显示加载状态
        }
        
        viewModel.error.observe(this) { error ->
            if (error.isNotEmpty()) {
                showSnackbar(error)
            }
        }
    }
    
    private fun loadQuestion() {
        // 从Intent获取问题，如果没有则从ViewModel加载
        val question = intent.getStringExtra("tech_question")
        if (question != null) {
            binding.tvQuestion.text = question
        } else {
            val docId = intent.getStringExtra("doc_id") ?: "mock-doc-id-12345"
            val jobTitle = intent.getStringExtra("job_title") ?: "Software Engineer"
            viewModel.loadTechQuestion(docId, jobTitle)
        }
        
        Log.d(TAG, "Loading question for job title: ${intent.getStringExtra("job_title")}")
    }
    
    private fun showSnackbar(message: String) {
        Snackbar.make(binding.root, message, Snackbar.LENGTH_LONG).show()
    }
} 