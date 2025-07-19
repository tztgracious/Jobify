package com.chatwaifu.mobile.ui.questions

import android.content.Intent
import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import com.chatwaifu.mobile.databinding.ActivityTipsBinding
import com.chatwaifu.mobile.ui.welcome.WelcomeActivity

class TipsActivity : AppCompatActivity() {
    private lateinit var binding: ActivityTipsBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityTipsBinding.inflate(layoutInflater)
        setContentView(binding.root)

        val answers = intent.getStringArrayListExtra("answers") ?: arrayListOf()
        val tips = buildTips(answers)
        binding.tvTipsContent.text = tips

        binding.btnBackHome.setOnClickListener {
            val intent = Intent(this, WelcomeActivity::class.java)
            intent.flags = Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_NEW_TASK
            startActivity(intent)
            finish()
        }
    }

    private fun buildTips(answers: List<String>): String {
        // 简单拼接tips，后续可根据后端返回优化
        return "Thank you for completing the interview!\n\nYour answers:\n" +
                answers.mapIndexed { i, ans -> "Q${i+1}: $ans" }.joinToString("\n") +
                "\n\nTips: Be confident, answer concisely, and highlight your strengths!"
    }
} 