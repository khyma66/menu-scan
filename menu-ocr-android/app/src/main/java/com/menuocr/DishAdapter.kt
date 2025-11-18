package com.menuocr

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
import com.menuocr.databinding.ItemDishBinding

// Updated data class for DoorDash-like dish items
data class DishItem(
    val name: String,
    val description: String,
    val price: String,
    val imageRes: Int = android.R.drawable.ic_menu_gallery
)

class DishAdapter : RecyclerView.Adapter<DishAdapter.DishViewHolder>() {

    private val dishes = mutableListOf<DishItem>()

    fun updateData(dishItems: List<DishItem>) {
        dishes.clear()
        dishes.addAll(dishItems)
        notifyDataSetChanged()
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): DishViewHolder {
        val binding = ItemDishBinding.inflate(
            LayoutInflater.from(parent.context), parent, false
        )
        return DishViewHolder(binding)
    }

    override fun onBindViewHolder(holder: DishViewHolder, position: Int) {
        holder.bind(dishes[position])
    }

    override fun getItemCount(): Int = dishes.size

    class DishViewHolder(private val binding: ItemDishBinding) : RecyclerView.ViewHolder(binding.root) {
        fun bind(dish: DishItem) {
            binding.tvDishName.text = dish.name
            binding.tvDishDescription.text = dish.description
            binding.tvPrice.text = dish.price
            
            // Set dish image placeholder
            binding.ivDishImage.setImageResource(dish.imageRes)
            
            // Set click listener for quick add button
            binding.btnQuickAdd.setOnClickListener {
                // TODO: Implement add to cart functionality
                android.widget.Toast.makeText(
                    itemView.context,
                    "Added ${dish.name} to cart",
                    android.widget.Toast.LENGTH_SHORT
                ).show()
            }
        }
    }
}