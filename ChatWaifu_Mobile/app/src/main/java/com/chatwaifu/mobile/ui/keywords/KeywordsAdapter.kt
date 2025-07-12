package com.chatwaifu.mobile.ui.keywords

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
import com.chatwaifu.mobile.R

class KeywordsAdapter(
    private val keywords: List<String>,
    private val onItemClick: (String) -> Unit = {}
) : RecyclerView.Adapter<KeywordsAdapter.KeywordViewHolder>() {

    // ViewHolder 类
    inner class KeywordViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val textView: TextView = itemView.findViewById(R.id.tvKeyword)

        fun bind(keyword: String) {
            textView.text = keyword
            itemView.setOnClickListener { onItemClick(keyword) }
        }
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): KeywordViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_keyword, parent, false)
        return KeywordViewHolder(view)
    }

    override fun onBindViewHolder(holder: KeywordViewHolder, position: Int) {
        holder.bind(keywords[position])
    }

    override fun getItemCount() = keywords.size
}