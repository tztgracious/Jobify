package com.chatwaifu.mobile.ui.questions

import android.Manifest
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Bundle
import android.os.CountDownTimer
import android.util.Log
import android.view.View
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.camera.core.CameraSelector
import androidx.camera.core.Preview
import androidx.camera.core.VideoCapture
import androidx.camera.core.VideoCapture.OutputFileOptions
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.core.content.ContextCompat
import com.chatwaifu.mobile.R
import com.chatwaifu.mobile.databinding.ActivityVideoAnswerBinding
import java.io.File
import java.text.SimpleDateFormat
import java.util.*
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors

class VideoAnswerActivity : AppCompatActivity() {
    private lateinit var binding: ActivityVideoAnswerBinding
    private var videoCapture: VideoCapture? = null
    private lateinit var cameraExecutor: ExecutorService
    private var outputUri: Uri? = null
    private var timer: CountDownTimer? = null
    private var isRecording = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityVideoAnswerBinding.inflate(layoutInflater)
        setContentView(binding.root)

        cameraExecutor = Executors.newSingleThreadExecutor()
        startCamera()
        setupUI()
    }

    private fun setupUI() {
        binding.btnStartRecord.setOnClickListener {
            if (!isRecording) {
                startRecording()
            } else {
                stopRecording()
            }
        }
        binding.btnFinish.setOnClickListener {
            finish()
        }
        binding.btnStartRecord.text = getString(R.string.start_recording)
        binding.btnFinish.text = getString(R.string.finish)
        binding.tvTimer.text = "60s"
        updateUI(false)
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
        val outputOptions = OutputFileOptions.Builder(videoFile).build()
        updateUI(true)
        isRecording = true
        timer = object : CountDownTimer(60_000, 1000) {
            override fun onTick(millisUntilFinished: Long) {
                binding.tvTimer.text = "${millisUntilFinished / 1000}s"
            }
            override fun onFinish() {
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
                        Toast.makeText(this@VideoAnswerActivity, getString(R.string.video_saved), Toast.LENGTH_SHORT).show()
                        updateUI(false)
                    }
                }
                override fun onError(videoCaptureError: Int, message: String, cause: Throwable?) {
                    runOnUiThread {
                        Toast.makeText(this@VideoAnswerActivity, getString(R.string.video_error) + ": $message", Toast.LENGTH_SHORT).show()
                        updateUI(false)
                    }
                }
            }
        )
    }

    private fun stopRecording() {
        videoCapture?.stopRecording()
        timer?.cancel()
        isRecording = false
        binding.tvTimer.text = "60s"
        updateUI(false)
    }

    private fun updateUI(recording: Boolean) {
        binding.btnStartRecord.text = if (recording) getString(R.string.stop_recording) else getString(R.string.start_recording)
        binding.btnStartRecord.isEnabled = true
        binding.btnFinish.isEnabled = !recording
        binding.tvTimer.visibility = View.VISIBLE
    }

    override fun onDestroy() {
        super.onDestroy()
        cameraExecutor.shutdown()
        timer?.cancel()
    }
} 