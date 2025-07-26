package com.chatwaifu.mobile.ui.techinterview

import android.content.Intent
import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import androidx.activity.viewModels
import com.chatwaifu.mobile.R
import com.chatwaifu.mobile.databinding.ActivityTechSolutionBinding
import android.util.Log

class TechSolutionActivity : AppCompatActivity() {

    private lateinit var binding: ActivityTechSolutionBinding
    private val viewModel: TechSolutionViewModel by viewModels()
    private val TAG = "TechSolutionActivity"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityTechSolutionBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setupButtons()
        setupObservers()
        loadSolution()
    }

    private fun setupButtons() {
        // 返回按钮回到 TechInterviewActivity
        binding.btnBack.setOnClickListener {
            val docId = intent.getStringExtra("doc_id") ?: "mock-doc-id-12345"
            val keywords = intent.getStringArrayExtra("keywords") ?: arrayOf("Java", "Kotlin", "Android", "REST API")
            val jobTitle = intent.getStringExtra("job_title") ?: "Software Engineer"
            val question = intent.getStringExtra("tech_question") ?: getString(R.string.sample_tech_question)
            
            val intent = Intent(this, TechInterviewActivity::class.java).apply {
                putExtra("doc_id", docId)
                putExtra("keywords", keywords)
                putExtra("job_title", jobTitle)
                putExtra("tech_question", question)
                flags = Intent.FLAG_ACTIVITY_CLEAR_TOP
            }
            startActivity(intent)
            finish()
        }

        // 下一步按钮跳转到 AnswerModeSelectActivity
        binding.btnNext.setOnClickListener {
            // 获取传递的参数
            val docId = intent.getStringExtra("doc_id") ?: "mock-doc-id-12345"
            val keywords = intent.getStringArrayExtra("keywords") ?: arrayOf("Java", "Kotlin", "Android", "REST API")
            val jobTitle = intent.getStringExtra("job_title") ?: "Software Engineer"
            
            // 跳转到 AnswerModeSelectActivity
            val intent = Intent(this, com.chatwaifu.mobile.ui.answermode.AnswerModeSelectActivity::class.java).apply {
                putExtra("doc_id", docId)
                putExtra("keywords", keywords)
                putExtra("job_title", jobTitle)
            }
            startActivity(intent)
        }
    }

    private fun setupObservers() {
        viewModel.solution.observe(this) { solution ->
            binding.tvStandardAnswer.text = solution.standardAnswer
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

    private fun loadSolution() {
        // 从Intent获取数据
        val question = intent.getStringExtra("tech_question") ?: getString(R.string.sample_tech_question)
        val answer = intent.getStringExtra("tech_answer") ?: getString(R.string.sample_user_answer)
        
        // 设置问题和答案
        binding.tvQuestion.text = question
        binding.tvYourAnswer.text = answer
        
        // 从ViewModel加载解决方案
        val docId = intent.getStringExtra("doc_id") ?: "mock-doc-id-12345"
        val jobTitle = intent.getStringExtra("job_title") ?: "Software Engineer"
        viewModel.loadSolution(docId, jobTitle, question, answer)
        
        Log.d(TAG, "Loading solution for question: $question")
    }

    private fun showSnackbar(message: String) {
        com.google.android.material.snackbar.Snackbar.make(binding.root, message, com.google.android.material.snackbar.Snackbar.LENGTH_LONG).show()
    }
} 