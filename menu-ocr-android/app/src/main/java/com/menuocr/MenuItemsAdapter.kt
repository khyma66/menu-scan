package com.menuocr

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView

class MenuItemsAdapter : RecyclerView.Adapter<MenuItemsAdapter.MenuItemViewHolder>() {

    private var menuItems: List<PersonalizedDish> = emptyList()

    fun updateItems(items: List<PersonalizedDish>) {
        menuItems = items
        notifyDataSetChanged()
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): MenuItemViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_menu_result, parent, false)
        return MenuItemViewHolder(view)
    }

    override fun onBindViewHolder(holder: MenuItemViewHolder, position: Int) {
        val item = menuItems[position]
        holder.bind(item, position + 1)
    }

    override fun getItemCount(): Int = menuItems.size

    class MenuItemViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val itemNumber: TextView = itemView.findViewById(R.id.item_number)
        private val itemName: TextView = itemView.findViewById(R.id.item_name)
        private val itemPrice: TextView = itemView.findViewById(R.id.item_price)
        private val itemDescription: TextView = itemView.findViewById(R.id.item_description)
        private val itemCategory: TextView = itemView.findViewById(R.id.item_category)

        private val itemRecommendation: TextView = itemView.findViewById(R.id.item_recommendation)
        private val itemRiskSummary: TextView = itemView.findViewById(R.id.item_risk_summary)
        private val itemHealthScore: TextView = itemView.findViewById(R.id.item_health_score)

        fun bind(menuItem: PersonalizedDish, number: Int) {
            itemNumber.text = number.toString()
            itemName.text = menuItem.dish_name

            if (menuItem.price != null) {
                itemPrice.text = "$${menuItem.price}"
                itemPrice.visibility = View.VISIBLE
            } else {
                itemPrice.visibility = View.GONE
            }

            val ingredients = menuItem.ingredients
            if (!ingredients.isNullOrEmpty()) {
                itemDescription.text = ingredients
                itemDescription.visibility = View.VISIBLE
            } else {
                itemDescription.visibility = View.GONE
            }

            itemCategory.visibility = View.GONE

            val level = menuItem.recommendation_level
            if (!level.isNullOrEmpty()) {
                itemRecommendation.text = "Recommendation: $level"
                itemRecommendation.visibility = View.VISIBLE
            } else {
                itemRecommendation.visibility = View.GONE
            }

            val summary = menuItem.risk_summary
            if (!summary.isNullOrEmpty()) {
                itemRiskSummary.text = summary
                itemRiskSummary.visibility = View.VISIBLE
            } else {
                itemRiskSummary.visibility = View.GONE
            }

            val score = menuItem.health_score
            if (score != null) {
                itemHealthScore.text = "Health score: $score"
                itemHealthScore.visibility = View.VISIBLE
            } else {
                itemHealthScore.visibility = View.GONE
            }
        }
    }
}