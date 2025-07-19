package com.chatwaifu.mobile.ui.keywords

import android.content.Intent
import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import androidx.activity.viewModels
import androidx.recyclerview.widget.LinearLayoutManager
import com.chatwaifu.mobile.ChatActivity
import com.chatwaifu.mobile.databinding.ActivityKeywordsBinding
import com.chatwaifu.mobile.ui.resume.UploadResumeActivity
import com.google.android.flexbox.FlexboxLayout
import android.widget.TextView
import android.view.ViewGroup
import android.view.LayoutInflater
import android.graphics.drawable.GradientDrawable
import android.graphics.Color
import android.util.Log
import android.view.View
import com.google.android.material.snackbar.Snackbar

class KeywordsActivity : AppCompatActivity() {

    private lateinit var binding: ActivityKeywordsBinding
    private val viewModel: KeywordsViewModel by viewModels()
    private val TAG = "KeywordsActivity"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityKeywordsBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setupButtons()
        setupObservers()
        
        // 获取doc_id并加载关键词
        val docId = intent.getStringExtra("doc_id") ?: "mock-doc-id-12345"
        Log.d(TAG, "Loading keywords for doc_id: $docId")
        
        // TODO: 使用真正的API调用
        /*
        viewModel.loadKeywords(docId)
        */
        
        // 暂时使用模拟数据
        val keywords = intent.getStringArrayExtra("keywords") ?: arrayOf("Java", "Kotlin", "Android", "REST API")
        displayKeywords(keywords.toList())
    }
    
    private fun setupButtons() {
        // 返回按钮直接回到 UploadResumeActivity
        binding.btnBack.setOnClickListener {
            startActivity(Intent(this, UploadResumeActivity::class.java).apply {
                flags = Intent.FLAG_ACTIVITY_CLEAR_TOP // 清除返回栈
            })
            finish()
        }

        // 下一步按钮
        binding.btnNext.setOnClickListener {
            val docId = intent.getStringExtra("doc_id") ?: "mock-doc-id-12345"
            startActivity(Intent(this, ChatActivity::class.java).apply {
                putExtra("interview_mode", true)
                putExtra("doc_id", docId) // 传递doc_id到聊天界面
            })
        }
    }
    
    private fun setupObservers() {
        // TODO: 观察ViewModel的结果
        /*
        viewModel.keywords.observe(this) { keywords ->
            displayKeywords(keywords)
        }
        
        viewModel.isLoading.observe(this) { isLoading ->
            binding.progressBar.visibility = if (isLoading) View.VISIBLE else View.GONE
        }
        
        viewModel.error.observe(this) { error ->
            if (error.isNotEmpty()) {
                showSnackbar(error)
            }
        }
        */
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
}