# =============================================================================
# MenuOCR – ProGuard / R8 rules
# =============================================================================
# Keep line numbers and source-file names so Crashlytics stack traces are
# human-readable. R8 renames the attribute so the original filename is hidden.
-keepattributes SourceFile,LineNumberTable
-renamesourcefileattribute SourceFile

# Keep all annotations – required by many reflection-based libraries.
-keepattributes *Annotation*
-keepattributes Signature
-keepattributes Exceptions
-keepattributes InnerClasses
-keepattributes EnclosingMethod

# =============================================================================
# App – Data / DTO classes used for JSON serialisation
# =============================================================================
# Keep all data classes in the model/data packages so Gson and kotlinx.json
# can still read them at runtime. Only these packages are kept – the rest of
# the app IS obfuscated.
-keep class com.menuocr.data.** { *; }
-keep class com.menuocr.model.** { *; }
-keep class com.menuocr.api.** { *; }
# Fallback: keep any class that carries @Serializable or @SerialName
-keepclassmembers @kotlinx.serialization.Serializable class ** { *; }

# =============================================================================
# Kotlin
# =============================================================================
-keep class kotlin.** { *; }
-keep class kotlin.Metadata { *; }
-dontwarn kotlin.**
-keepclassmembers class **$WhenMappings { <fields>; }
-keepclassmembernames class kotlinx.** { volatile <fields>; }

# =============================================================================
# Kotlin Serialization (kotlinx.serialization)
# =============================================================================
-keepclassmembers class kotlinx.serialization.json.** { *** serializer(...); }
-keepclasseswithmembers class ** {
    kotlinx.serialization.KSerializer serializer(...);
}
-keep,includedescriptorclasses class com.menuocr.**$$serializer { *; }
-keepclassmembers class com.menuocr.** {
    *** Companion;
}
-keepclasseswithmembers class com.menuocr.** {
    kotlinx.serialization.KSerializer serializer(...);
}
-dontwarn kotlinx.serialization.**

# =============================================================================
# Coroutines
# =============================================================================
-keepnames class kotlinx.coroutines.internal.MainDispatcherFactory {}
-keepnames class kotlinx.coroutines.CoroutineExceptionHandler {}
-keepclassmembernames class kotlinx.** { volatile <fields>; }
-dontwarn kotlinx.coroutines.**

# =============================================================================
# Retrofit 2 + OkHttp 3
# =============================================================================
-dontwarn okhttp3.**
-dontwarn okio.**
-keep class retrofit2.** { *; }
-keep interface retrofit2.** { *; }
-keepclasseswithmembers class * {
    @retrofit2.http.* <methods>;
}
-keepclassmembers,allowshrinking,allowobfuscation interface * {
    @retrofit2.http.* <methods>;
}
-dontwarn retrofit2.**

# =============================================================================
# Gson
# =============================================================================
-keepattributes Signature
-keep class com.google.gson.** { *; }
-keep class sun.misc.Unsafe { *; }
-keep class com.google.gson.stream.** { *; }
# Prevent R8 stripping TypeToken subclasses
-keep class * extends com.google.gson.TypeAdapter
-keep class * implements com.google.gson.TypeAdapterFactory
-keep class * implements com.google.gson.JsonDeserializer
-keep class * implements com.google.gson.JsonSerializer

# =============================================================================
# Ktor
# =============================================================================
-keep class io.ktor.** { *; }
-dontwarn io.ktor.**
-keep class kotlinx.coroutines.** { *; }

# =============================================================================
# Supabase (jan-tennert client)
# =============================================================================
-keep class io.github.jan.supabase.** { *; }
-dontwarn io.github.jan.supabase.**
# Supabase uses reflection on your user model – keep any class annotated with
# @Serializable (covered above) or any class passed to supabase DSL.

# =============================================================================
# Glide
# =============================================================================
-keep public class * implements com.bumptech.glide.module.GlideModule
-keep class * extends com.bumptech.glide.module.AppGlideModule { <init>(...); }
-keep public enum com.bumptech.glide.load.ImageHeaderParser$** {
    **[] $VALUES;
    public *;
}
-keep class com.bumptech.glide.load.data.ParcelFileDescriptorRewinder$InternalRewinder {
    *** rewind();
}
-dontwarn com.bumptech.glide.**

# =============================================================================
# Room
# =============================================================================
-keep class * extends androidx.room.RoomDatabase { *; }
-keep @androidx.room.Entity class * { *; }
-keep @androidx.room.Dao class * { *; }
-dontwarn androidx.room.**

# =============================================================================
# WorkManager
# =============================================================================
-keep class * extends androidx.work.Worker
-keep class * extends androidx.work.ListenableWorker {
    public <init>(android.content.Context, androidx.work.WorkerParameters);
}
-dontwarn androidx.work.**

# =============================================================================
# MapLibre
# =============================================================================
-keep class org.maplibre.** { *; }
-dontwarn org.maplibre.**

# =============================================================================
# Firebase Analytics
# =============================================================================
-keep class com.google.firebase.analytics.** { *; }
-dontwarn com.google.firebase.analytics.**

# =============================================================================
# Firebase Crashlytics
# =============================================================================
# Crash reports use the mapping file; Crashlytics uploads it automatically.
# Preserve the mapping file upload metadata.
-keep class com.google.firebase.crashlytics.** { *; }
-dontwarn com.google.firebase.crashlytics.**
# Keep custom exception classes so crash reports show readable names.
-keep public class * extends java.lang.Exception

# =============================================================================
# Google Play Services
# =============================================================================
-keep class com.google.android.gms.** { *; }
-dontwarn com.google.android.gms.**

# =============================================================================
# WebView JavaScript interface (if added in the future)
# =============================================================================
#-keepclassmembers class <fully.qualified.WebViewClient> {
#    public *;
#}
