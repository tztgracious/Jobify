package com.chatwaifu.mobile.ui.welcome

import android.content.Intent
import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import com.chatwaifu.mobile.databinding.ActivityWelcomeBinding
import com.chatwaifu.mobile.ui.resume.UploadResumeActivity

class WelcomeActivity : AppCompatActivity() {
    private lateinit var binding: ActivityWelcomeBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityWelcomeBinding.inflate(layoutInflater)
        setContentView(binding.root)

        // Button
        binding.startButton.setOnClickListener {
            // Jump to ResumeActivity (正确的流程)
            startActivity(Intent(this, UploadResumeActivity::class.java))
            finish()  // Close WelcomeActivity
        }
    }
}