package com.chatwaifu.mobile.ui.questions

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.os.CountDownTimer
import android.util.Log
import android.view.View
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.camera.core.CameraSelector
import androidx.camera.core.Preview
import androidx.camera.core.VideoCapture
import androidx.camera.core.VideoCapture.OutputFileOptions
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.core.content.ContextCompat
import androidx.lifecycle.lifecycleScope
import com.chatwaifu.mobile.R
import com.chatwaifu.mobile.databinding.ActivityVideoAnswerBinding
import com.chatwaifu.mobile.data.network.VideoUploadService
import kotlinx.coroutines.launch
import java.io.File
import java.text.SimpleDateFormat
import java.util.*
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors
import android.content.ContentValues
import android.provider.MediaStore

class VideoAnswerActivity : AppCompatActivity() {
    private lateinit var binding: ActivityVideoAnswerBinding
    private var videoCapture: VideoCapture? = null
    private lateinit var cameraExecutor: ExecutorService
    private var outputUri: Uri? = null
    private var outputFile: File? = null
    private var timer: CountDownTimer? = null
    private var isRecording = false
    private var isUploading = false
    private lateinit var videoUploadService: VideoUploadService
    
    // Intent parameters
    private var sessionId: String = ""
    private var questionIndex: Int = 0
    private var questionText: String = ""

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityVideoAnswerBinding.inflate(layoutInflater)
        setContentView(binding.root)

        // Get parameters from intent
        sessionId = intent.getStringExtra("session_id") ?: "default_session"
        questionIndex = intent.getIntExtra("question_index", 0)
        questionText = intent.getStringExtra("question_text") ?: "Please answer this question"

        cameraExecutor = Executors.newSingleThreadExecutor()
        videoUploadService = VideoUploadService(this)
        
        startCamera()
        setupUI()
        
        // Auto start recording after camera setup
        binding.root.postDelayed({
            startRecording()
        }, 1000)
    }

    private fun setupUI() {
        binding.btnAction.setOnClickListener {
            if (isRecording) {
                stopRecording()
            }
        }
        
        // Display question text
        binding.tvQuestion.text = "Question ${questionIndex + 1}: $questionText"
        
        // Set initial UI to recording state since we auto-start recording
        updateUI(true, false)
    }

    private fun startCamera() {
        val cameraProviderFuture = ProcessCameraProvider.getInstance(this)
        cameraProviderFuture.addListener({
            val cameraProvider = cameraProviderFuture.get()
            val preview = Preview.Builder().build().also {
                it.setSurfaceProvider(binding.previewView.surfaceProvider)
            }
            videoCapture = VideoCapture.Builder().build()
            val cameraSelector = CameraSelector.DEFAULT_FRONT_CAMERA
            try {
                cameraProvider.unbindAll()
                cameraProvider.bindToLifecycle(
                    this, cameraSelector, preview, videoCapture
                )
            } catch (e: Exception) {
                Log.e("VideoAnswer", "Camera binding failed", e)
            }
        }, ContextCompat.getMainExecutor(this))
    }

    private fun startRecording() {
        val videoFile = File(
            externalCacheDir,
            "video_${SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US).format(Date())}.mp4"
        )
        outputFile = videoFile
        val outputOptions = OutputFileOptions.Builder(videoFile).build()
        
        isRecording = true
        // UI is already set to recording state in setupUI()
        
        // Start 60-second countdown
        timer = object : CountDownTimer(60_000, 1000) {
            override fun onTick(millisUntilFinished: Long) {
                val seconds = millisUntilFinished / 1000
                binding.tvTimer.text = "${seconds}s"
            }
            override fun onFinish() {
                // Auto stop when time is up
                stopRecording()
            }
        }.start()
        
        videoCapture?.startRecording(
            outputOptions,
            ContextCompat.getMainExecutor(this),
            object : VideoCapture.OnVideoSavedCallback {
                override fun onVideoSaved(outputFileResults: VideoCapture.OutputFileResults) {
                    outputUri = outputFileResults.savedUri ?: Uri.fromFile(videoFile)
                    runOnUiThread {
                        saveVideoToGallery(outputFile ?: return@runOnUiThread)
                    }
                }
                override fun onError(videoCaptureError: Int, message: String, cause: Throwable?) {
                    runOnUiThread {
                        isRecording = false
                        updateUI(false, false)
                        Toast.makeText(this@VideoAnswerActivity, "Recording error: $message", Toast.LENGTH_SHORT).show()
                        // Even if recording fails, return to next question
                        finishWithResult(false)
                    }
                }
            }
        )
    }

    // 新增：保存视频到相册
    private fun saveVideoToGallery(file: File) {
        val resolver = applicationContext.contentResolver
        val videoCollection = if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.Q) {
            MediaStore.Video.Media.getContentUri(MediaStore.VOLUME_EXTERNAL_PRIMARY)
        } else {
            MediaStore.Video.Media.EXTERNAL_CONTENT_URI
        }
        val newVideo = ContentValues().apply {
            put(MediaStore.Video.Media.DISPLAY_NAME, file.name)
            put(MediaStore.Video.Media.MIME_TYPE, "video/mp4")
            put(MediaStore.Video.Media.RELATIVE_PATH, "Movies/ChatWaifu")
            put(MediaStore.Video.Media.IS_PENDING, 1)
        }
        val videoUri = resolver.insert(videoCollection, newVideo)
        videoUri?.let { uri ->
            resolver.openOutputStream(uri)?.use { outputStream ->
                file.inputStream().use { inputStream ->
                    inputStream.copyTo(outputStream)
                }
            }
            newVideo.clear()
            newVideo.put(MediaStore.Video.Media.IS_PENDING, 0)
            resolver.update(uri, newVideo, null, null)
            runOnUiThread {
                Toast.makeText(this, "Video saved to gallery!", Toast.LENGTH_SHORT).show()
                finishWithResult(true)
            }
        }
    }

    private fun stopRecording() {
        if (isRecording) {
            videoCapture?.stopRecording()
            timer?.cancel()
            isRecording = false
            // UI will be updated in onVideoSaved callback
        }
    }
    
    private fun uploadVideo() {
        outputFile?.let { file ->
            if (file.exists()) {
                isUploading = true
                updateUI(false, true)
                
                lifecycleScope.launch {
                    videoUploadService.uploadVideoAnswer(
                        id = sessionId,
                        questionIndex = questionIndex,
                        question = questionText,
                        videoFile = file,
                        onSuccess = { response ->
                            runOnUiThread {
                                Toast.makeText(
                                    this@VideoAnswerActivity,
                                    "Upload successful! Progress: ${response.progress}%",
                                    Toast.LENGTH_SHORT
                                ).show()
                                finishWithResult(true)
                            }
                        },
                        onError = { errorMsg ->
                            runOnUiThread {
                                Toast.makeText(
                                    this@VideoAnswerActivity,
                                    "Upload failed, but continuing...",
                                    Toast.LENGTH_SHORT
                                ).show()
                                // Even if upload fails, return to next question
                                finishWithResult(false)
                            }
                        }
                    )
                }
            }
        }
    }
    
    private fun finishWithResult(success: Boolean) {
        val resultIntent = Intent().apply {
            putExtra("upload_success", success)
            putExtra("progress", if (success) 100.0 else 0.0)
            putExtra("is_completed", false)
            putExtra("message", if (success) "Upload successful" else "Upload failed")
        }
        setResult(RESULT_OK, resultIntent)
        finish()
    }

    private fun updateUI(recording: Boolean, uploading: Boolean) {
        when {
            recording -> {
                binding.btnAction.text = "STOP"
                binding.btnAction.isEnabled = true
                binding.tvTimer.visibility = View.VISIBLE
            }
            uploading -> {
                binding.btnAction.text = "UPLOADING..."
                binding.btnAction.isEnabled = false
                binding.tvTimer.visibility = View.VISIBLE
                binding.tvTimer.text = "Uploading..."
            }
            else -> {
                binding.btnAction.text = "START"
                binding.btnAction.isEnabled = true
                binding.tvTimer.visibility = View.VISIBLE
                binding.tvTimer.text = "60s"
            }
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        cameraExecutor.shutdown()
        timer?.cancel()
    }
} 