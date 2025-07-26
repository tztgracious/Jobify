package com.chatwaifu.mobile.ui.solution

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import com.chatwaifu.mobile.databinding.ActivitySolutionBinding

class SolutionActivity : AppCompatActivity() {
    private lateinit var binding: ActivitySolutionBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivitySolutionBinding.inflate(layoutInflater)
        setContentView(binding.root)

        // 从intent获取传递的数据
        val questions = intent.getStringArrayListExtra("questions") ?: arrayListOf()
        val answers = intent.getStringArrayListExtra("answers") ?: arrayListOf()
        val solutions = intent.getStringArrayListExtra("solutions") ?: arrayListOf()

        // 填充UI
        if (questions.size >= 1) {
            binding.tvQuestion1.text = "Question 1: ${questions.getOrNull(0) ?: ""}"
            binding.tvYourAnswer1.text = "Your Answer: ${answers.getOrNull(0) ?: ""}"
            binding.tvStandardAnswer1.text = "Solution: ${solutions.getOrNull(0) ?: ""}"
        }
        
        if (questions.size >= 2) {
            binding.tvQuestion2.text = "Question 2: ${questions.getOrNull(1) ?: ""}"
            binding.tvYourAnswer2.text = "Your Answer: ${answers.getOrNull(1) ?: ""}"
            binding.tvStandardAnswer2.text = "Solution: ${solutions.getOrNull(1) ?: ""}"
        }
        
        if (questions.size >= 3) {
            binding.tvQuestion3.text = "Question 3: ${questions.getOrNull(2) ?: ""}"
            binding.tvYourAnswer3.text = "Your Answer: ${answers.getOrNull(2) ?: ""}"
            binding.tvStandardAnswer3.text = "Solution: ${solutions.getOrNull(2) ?: ""}"
        }

        binding.btnBack.setOnClickListener { finish() }
        binding.btnNext.setOnClickListener {
            val intent = android.content.Intent(this, com.chatwaifu.mobile.ui.tips.TipsActivity::class.java)
            // 传递数据给TipsActivity
            intent.putStringArrayListExtra("questions", questions)
            intent.putStringArrayListExtra("answers", answers)
            intent.putStringArrayListExtra("solutions", solutions)
            startActivity(intent)
            finish()
        }
    }
} 