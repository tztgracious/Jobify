package com.chatwaifu.mobile.ui.resume

import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.util.Log
import android.view.View
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.activity.viewModels
import android.app.AlertDialog
import com.chatwaifu.mobile.databinding.ActivityUploadResumeBinding
import com.google.android.material.snackbar.Snackbar
import com.chatwaifu.mobile.ui.welcome.WelcomeActivity
import com.chatwaifu.mobile.ChatActivity
import com.chatwaifu.mobile.ui.keywords.KeywordsActivity
import com.chatwaifu.mobile.R

class UploadResumeActivity : AppCompatActivity() {

    private lateinit var binding: ActivityUploadResumeBinding
    private var selectedFileUri: Uri? = null
    private val TAG = "UploadResumeActivity"
    private var loadingDialog: AlertDialog? = null
    
    private val viewModel: ResumeViewModel by viewModels()

    private val filePickerLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        try {
        if (result.resultCode == Activity.RESULT_OK) {
            result.data?.data?.let { uri ->
                selectedFileUri = uri
                    try {
                        contentResolver.takePersistableUriPermission(
                            uri,
                            Intent.FLAG_GRANT_READ_URI_PERMISSION
                        )
                    } catch (e: Exception) {
                        e.printStackTrace()
                        showSnackbar("文件授权失败，可能无法正常读取")
                    }
                Log.d(TAG, "File selected: $uri")

                // 只更新绿色提示，不再更改btnUpload文本
                val fileName = uri.lastPathSegment?.substringAfterLast("/") ?: "unknown_file.pdf"
                binding.tvFileInfo.text = "File: $fileName"
                binding.tvFileInfo.visibility = View.VISIBLE
                binding.btnNext.isEnabled = true

                // 选择文件后按钮文字变为'Reselect'
                binding.btnUpload.text = "Reselect"

                showSnackbar("PDF file selected")
            }
        } else {
            Log.d(TAG, "File selection cancelled or failed.")
            }
        } catch (e: Exception) {
            e.printStackTrace()
            showSnackbar("File selection error: ${e.message}")
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityUploadResumeBinding.inflate(layoutInflater)
        setContentView(binding.root)
        Log.d(TAG, "Activity created.")

        // 新增：进入页面即请求存储权限
        if (!com.chatwaifu.vits.utils.permission.PermissionUtils.checkStoragePermission(this)) {
            com.chatwaifu.vits.utils.permission.PermissionUtils.requestStoragePermission(this)
        }
        // Initialize UI state
        binding.tvFileInfo.visibility = View.GONE
        setupButtons()
        setupObservers()
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
            try {
            if (selectedFileUri == null) {
                showSnackbar("Please upload your resume first!")
                return@setOnClickListener
            }
            // TODO: 使用真正的API调用
            /*
            showLoadingDialog()
            viewModel.uploadResume(this, selectedFileUri!!)
            */
            // 暂时使用模拟数据
            showLoadingDialog()
            Handler(Looper.getMainLooper()).postDelayed({
                    try {
                hideLoadingDialog()
                val keywords = arrayOf("Java", "C++", "Python")
                startActivity(Intent(this, KeywordsActivity::class.java).apply {
                    putExtra("keywords", keywords)
                    putExtra("doc_id", "mock-doc-id-12345") // 传递模拟的doc_id
                })
                    } catch (e: Exception) {
                        e.printStackTrace()
                        showSnackbar("跳转失败: ${e.message}")
                    }
            }, 2000)
            } catch (e: Exception) {
                e.printStackTrace()
                showSnackbar("Error: ${e.message}")
            }
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
        val intent = Intent(Intent.ACTION_OPEN_DOCUMENT).apply {
            addCategory(Intent.CATEGORY_OPENABLE)
            type = "application/pdf"
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

    private fun showLoadingDialog() {
        if (loadingDialog == null) {
            loadingDialog = AlertDialog.Builder(this)
                .setView(R.layout.dialog_loading)
                .setCancelable(false)
                .create()
            loadingDialog?.window?.setBackgroundDrawableResource(android.R.color.transparent)
        }
        loadingDialog?.show()
    }

    private fun hideLoadingDialog() {
        loadingDialog?.dismiss()
    }
    
    private fun setupObservers() {
        // TODO: 观察ViewModel的结果
        /*
        viewModel.uploadResult.observe(this) { result ->
            hideLoadingDialog()
            when (result) {
                is ResumeViewModel.UploadResult.Success -> {
                    Log.d(TAG, "Upload successful, doc_id: ${result.docId}")
                    startActivity(Intent(this, KeywordsActivity::class.java).apply {
                        putExtra("doc_id", result.docId)
                    })
                }
                is ResumeViewModel.UploadResult.Error -> {
                    Log.e(TAG, "Upload failed: ${result.message}")
                    showSnackbar("Upload failed: ${result.message}")
                }
            }
        }
        
        viewModel.isLoading.observe(this) { isLoading ->
            if (isLoading) {
                showLoadingDialog()
            } else {
                hideLoadingDialog()
            }
        }
        */
    }

    companion object {
        const val EXTRA_RESUME_URI = "resume_uri"
    }
}
