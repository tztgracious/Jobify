package com.chatwaifu.mobile

import android.content.pm.PackageManager
import android.os.Bundle
import android.util.Log
import androidx.navigation.NavController
import androidx.navigation.fragment.NavHostFragment
import androidx.appcompat.app.AppCompatActivity
import androidx.compose.ui.platform.ComposeView
import androidx.lifecycle.ViewModelProvider
import com.chatwaifu.mobile.ui.base.ChatWaifuRootView
import com.chatwaifu.mobile.ui.showToast
import com.chatwaifu.mobile.ui.theme.ChatWaifu_MobileTheme

class ChatActivity : AppCompatActivity() {

    private val chatViewModel: ChatActivityViewModel by lazy {
        ViewModelProvider(this)[ChatActivityViewModel::class.java]
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // 接收答题模式参数
        val answerMode = intent.getStringExtra("answer_mode") ?: "text"
        Log.d("ChatActivity", "Received answer_mode: $answerMode")
        chatViewModel.setAnswerMode(answerMode)
        
        // 接收doc_id参数并传递给ViewModel
        val docId = intent.getStringExtra("doc_id")
        Log.d("ChatActivity", "Received doc_id: $docId")
        docId?.let { id ->
            Log.d("ChatActivity", "Setting doc_id in ViewModel: $id")
            chatViewModel.setDocId(id)
        } ?: run {
            Log.w("ChatActivity", "No doc_id received from intent")
        }
        
        setContentView(
            ComposeView(this).apply {
                setContent {
                    ChatWaifu_MobileTheme {
                        ChatWaifuRootView(
                            chatViewModel = chatViewModel,
                            onChannelListClick = {
                                findNavController().navigate(R.id.nav_channel_list)
                            },
                            onChatLogClick = {
                                findNavController().navigate(R.id.nav_chat_log)
                            },
                            onSettingClick = {
                                findNavController().navigate(R.id.nav_setting)
                            }
                        )
                    }
                }
            }
        )
        chatViewModel.refreshAllKeys()
        chatViewModel.mainLoop()
    }
    
    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (permissions.isNotEmpty() && grantResults.isNotEmpty() && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
            showToast("Permission granted")
        } else {
            showToast("Permission denied")
        }
    }
    
    private fun findNavController(): NavController {
        val navHostFragment = supportFragmentManager.findFragmentById(R.id.nav_host_fragment) as NavHostFragment
        return navHostFragment.navController
    }
}