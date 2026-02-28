package com.menuocr

import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.*
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView

class OcrResultsActivity : AppCompatActivity() {

    private lateinit var recyclerView: RecyclerView
    private lateinit var adapter: MenuItemsAdapter
    private lateinit var processingMethod: TextView
    private lateinit var processingTime: TextView
    private lateinit var rawTextSection: LinearLayout
    private lateinit var rawTextContent: TextView
    private lateinit var btnBack: Button
    private lateinit var btnAddAnother: Button

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_ocr_results)

        // Initialize views
        recyclerView = findViewById(R.id.recycler_menu_items)
        processingMethod = findViewById(R.id.processing_method)
        processingTime = findViewById(R.id.processing_time)
        rawTextSection = findViewById(R.id.raw_text_section)
        rawTextContent = findViewById(R.id.raw_text_content)
        btnBack = findViewById(R.id.btn_back)
        btnAddAnother = findViewById(R.id.btn_add_another)

        // Setup RecyclerView
        recyclerView.layoutManager = LinearLayoutManager(this)
        adapter = MenuItemsAdapter()
        recyclerView.adapter = adapter

        // Get data from intent
        val personalizedItems = intent.getSerializableExtra("personalized_items") as? ArrayList<PersonalizedDish> ?: arrayListOf()
        val rawText = intent.getStringExtra("raw_text") ?: ""
        val method = intent.getStringExtra("method") ?: "Unknown"
        val timeMs = intent.getIntExtra("processing_time", 0)

        // Display data
        adapter.updateItems(personalizedItems)
        processingMethod.text = "Processing Method: $method"
        processingTime.text = "Processing Time: ${timeMs}ms"

        if (rawText.isNotEmpty()) {
            rawTextContent.text = rawText
            rawTextSection.visibility = View.VISIBLE
        } else {
            rawTextSection.visibility = View.GONE
        }

        // Setup button listeners
        btnBack.setOnClickListener {
            finish() // Go back to previous activity
        }

        btnAddAnother.setOnClickListener {
            // Go back to OCR fragment to add another image
            val intent = Intent(this, DoorDashMainActivity::class.java)
            intent.flags = Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP
            startActivity(intent)
            finish()
        }
    }
}