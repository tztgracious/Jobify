package com.chatwaifu.mobile.ui.techinterview

import android.content.Intent
import android.os.Bundle
import android.widget.Button
import androidx.appcompat.app.AppCompatActivity
import com.chatwaifu.mobile.R

class TechInterviewActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_job_blank)

        val btnBack = findViewById<Button>(R.id.btnBack)
        val btnNext = findViewById<Button>(R.id.btnNext)

        btnBack.setOnClickListener {
            finish()
        }
        btnNext.setOnClickListener {
            val keywords = intent.getStringArrayExtra("keywords")
            val docId = intent.getStringExtra("doc_id")
            val intent = Intent(this, com.chatwaifu.mobile.ui.answertype.AnswerTypeSelectActivity::class.java).apply {
                if (keywords != null) putExtra("keywords", keywords)
                if (docId != null) putExtra("doc_id", docId)
            }
            startActivity(intent)
        }
    }
} 