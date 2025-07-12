package com.chatwaifu.mobile.ui.resume

import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.util.Log
import android.view.View
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import com.chatwaifu.mobile.databinding.ActivityUploadResumeBinding
import com.google.android.material.snackbar.Snackbar
import com.chatwaifu.mobile.ui.welcome.WelcomeActivity
import com.chatwaifu.mobile.ChatActivity
import com.chatwaifu.mobile.ui.keywords.KeywordsActivity

class UploadResumeActivity : AppCompatActivity() {

    private lateinit var binding: ActivityUploadResumeBinding
    private var selectedFileUri: Uri? = null
    private val TAG = "UploadResumeActivity"

    private val filePickerLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == Activity.RESULT_OK) {
            result.data?.data?.let { uri ->
                selectedFileUri = uri
                Log.d(TAG, "File selected: $uri")

                // Update the UI with the selected file name
                val fileName = uri.lastPathSegment?.substringAfterLast("/") ?: "unknown_file.pdf"
                binding.btnUpload.text = "Selected: $fileName"
                binding.tvFileInfo.text = "File: $fileName"
                binding.tvFileInfo.visibility = View.VISIBLE
                binding.btnNext.isEnabled = true

                showSnackbar("PDF file selected")
            }
        } else {
            Log.d(TAG, "File selection cancelled or failed.")
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityUploadResumeBinding.inflate(layoutInflater)
        setContentView(binding.root)
        Log.d(TAG, "Activity created.")

        // Initialize UI state
        binding.btnNext.isEnabled = false
        binding.tvFileInfo.visibility = View.GONE
        setupButtons()
    }

    private fun setupButtons() {
        binding.btnBack.setOnClickListener {
            Log.d(TAG, "Back button clicked.")
            navigateBackToWelcome()
        }

        binding.btnUpload.setOnClickListener {
            Log.d(TAG, "Upload button clicked.")
            openFilePicker()
        }


        binding.btnNext.setOnClickListener {
            val keywords = arrayOf("Java", "C++", "Python")
            startActivity(Intent(this, KeywordsActivity::class.java).apply {
                putExtra("keywords", keywords)
            })

        }
    }

    private fun navigateBackToWelcome() {
        val intent = Intent(this, WelcomeActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP
        }
        startActivity(intent)
        finish()
    }

    private fun openFilePicker() {
        val intent = Intent(Intent.ACTION_GET_CONTENT).apply {
            type = "application/pdf"
            addCategory(Intent.CATEGORY_OPENABLE)
        }
        filePickerLauncher.launch(intent)
    }

    private fun navigateToChatActivity(uri: Uri) {
        startActivity(Intent(this, ChatActivity::class.java).apply {
            putExtra(EXTRA_RESUME_URI, uri.toString())
        })
    }

    private fun showSnackbar(message: String) {
        Snackbar.make(binding.root, message, Snackbar.LENGTH_SHORT).show()
        Log.d(TAG, "Showing Snackbar: $message")
    }

    companion object {
        const val EXTRA_RESUME_URI = "resume_uri"
    }
}
