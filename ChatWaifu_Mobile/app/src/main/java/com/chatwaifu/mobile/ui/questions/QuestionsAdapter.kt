package com.chatwaifu.mobile.ui.questions

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.chatwaifu.mobile.R
import com.chatwaifu.mobile.databinding.ItemQuestionBinding

class QuestionsAdapter : ListAdapter<String, QuestionsAdapter.QuestionViewHolder>(QuestionDiffCallback()) {

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): QuestionViewHolder {
        val binding = ItemQuestionBinding.inflate(
            LayoutInflater.from(parent.context),
            parent,
            false
        )
        return QuestionViewHolder(binding)
    }

    override fun onBindViewHolder(holder: QuestionViewHolder, position: Int) {
        holder.bind(getItem(position), position + 1)
    }

    class QuestionViewHolder(private val binding: ItemQuestionBinding) : 
        RecyclerView.ViewHolder(binding.root) {
        
        fun bind(question: String, questionNumber: Int) {
            binding.tvQuestionNumber.text = binding.root.context.getString(R.string.question_number, questionNumber)
            binding.tvQuestionText.text = question
        }
    }

    private class QuestionDiffCallback : DiffUtil.ItemCallback<String>() {
        override fun areItemsTheSame(oldItem: String, newItem: String): Boolean {
            return oldItem == newItem
        }

        override fun areContentsTheSame(oldItem: String, newItem: String): Boolean {
            return oldItem == newItem
        }
    }
} 