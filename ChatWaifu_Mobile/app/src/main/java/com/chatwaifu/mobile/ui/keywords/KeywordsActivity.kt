package com.chatwaifu.mobile.ui.keywords

import android.content.Intent
import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.LinearLayoutManager
import com.chatwaifu.mobile.ChatActivity
import com.chatwaifu.mobile.databinding.ActivityKeywordsBinding
import com.chatwaifu.mobile.ui.resume.UploadResumeActivity

class KeywordsActivity : AppCompatActivity() {

    private lateinit var binding: ActivityKeywordsBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityKeywordsBinding.inflate(layoutInflater)
        setContentView(binding.root)

        // 返回按钮直接回到 UploadResumeActivity
        binding.btnBack.setOnClickListener {
            startActivity(Intent(this, UploadResumeActivity::class.java).apply {
                flags = Intent.FLAG_ACTIVITY_CLEAR_TOP // 清除返回栈
            })
            finish()
        }

        // 下一步按钮
        binding.btnNext.setOnClickListener {
            startActivity(Intent(this, ChatActivity::class.java))
        }

        // 设置关键词列表
        val keywords = intent.getStringArrayExtra("keywords") ?: arrayOf("Java", "Kotlin")
        binding.rvKeywords.apply {
            layoutManager = LinearLayoutManager(this@KeywordsActivity)
            adapter = KeywordsAdapter(keywords.toList())
        }
    }
}