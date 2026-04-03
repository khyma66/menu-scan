import java.util.Properties

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("kotlin-parcelize")
    id("org.jetbrains.kotlin.plugin.serialization") version "1.9.24"
    // Google Services – processes google-services.json into BuildConfig / resources
    // id("com.google.gms.google-services")
    // Crashlytics – uploads the R8 mapping file so crash stack traces are readable
    // id("com.google.firebase.crashlytics")
}

// ---------------------------------------------------------------------------
// Load release signing credentials from keystore.properties (never committed)
// ---------------------------------------------------------------------------
val keystorePropsFile = rootProject.file("keystore.properties")
val keystoreProps = Properties().apply {
    if (keystorePropsFile.exists()) load(keystorePropsFile.inputStream())
}

android {
    namespace = "com.menuocr"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.menuocr"
        minSdk = 24
        targetSdk = 35
        versionCode = 2       // increment for every Play Store release
        versionName = "1.0.1" // human-readable version shown on the store

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    // -----------------------------------------------------------------------
    // Signing – release builds use the keystore defined in keystore.properties
    // -----------------------------------------------------------------------
    signingConfigs {
        create("release") {
            if (keystoreProps.containsKey("storeFile")) {
                storeFile = file(keystoreProps["storeFile"] as String)
                storePassword = keystoreProps["storePassword"] as String
                keyAlias = keystoreProps["keyAlias"] as String
                keyPassword = keystoreProps["keyPassword"] as String
            }
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = true    // enable ProGuard/R8 code shrinking & obfuscation
            isShrinkResources = true  // remove unused resources
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
            if (keystoreProps.containsKey("storeFile")) {
                signingConfig = signingConfigs.getByName("release")
            }
        }
    }

    splits {
        abi {
            isEnable = true
            reset()
            include("arm64-v8a", "armeabi-v7a", "x86_64")
            isUniversalApk = false
        }
    }

    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
            excludes += "/META-INF/*.kotlin_module"
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_1_8
        targetCompatibility = JavaVersion.VERSION_1_8
    }

    kotlinOptions {
        jvmTarget = "1.8"
    }

    buildFeatures {
        viewBinding = true
        dataBinding = true
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.12.0")
    implementation("androidx.lifecycle:lifecycle-viewmodel-ktx:2.7.0")
    implementation("androidx.activity:activity-ktx:1.8.2")
    implementation("androidx.fragment:fragment-ktx:1.6.2")

    // UI
    implementation("androidx.appcompat:appcompat:1.6.1")
    implementation("com.google.android.material:material:1.11.0")
    implementation("androidx.constraintlayout:constraintlayout:2.1.4")
    implementation("androidx.recyclerview:recyclerview:1.3.2")
    implementation("androidx.browser:browser:1.7.0")

    // Google Play Services Location
    implementation("com.google.android.gms:play-services-location:21.0.1")
    
    // Google Play Services Auth (for Google Sign-In)
    implementation("com.google.android.gms:play-services-auth:20.7.0")

    // Image picker
    implementation("com.github.dhaval2404:imagepicker:2.1")

    // Supabase
    implementation("io.github.jan-tennert.supabase:gotrue-kt:2.1.4")
    implementation("io.github.jan-tennert.supabase:postgrest-kt:2.1.4")
    implementation("io.github.jan-tennert.supabase:storage-kt:2.1.4")
    
    // Ktor client for Supabase
    implementation("io.ktor:ktor-client-android:2.3.7")
    implementation("io.ktor:ktor-client-content-negotiation:2.3.7")
    implementation("io.ktor:ktor-serialization-kotlinx-json:2.3.7")
    
    // Kotlin serialization
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.6.2")

    // Networking
    implementation("com.squareup.retrofit2:retrofit:2.9.0")
    implementation("com.squareup.retrofit2:converter-gson:2.9.0")
    implementation("com.squareup.okhttp3:logging-interceptor:4.12.0")

    // Coroutines
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-play-services:1.7.3")

    // Glide for image loading
    implementation("com.github.bumptech.glide:glide:4.16.0")

    // Room database
    implementation("androidx.room:room-runtime:2.6.1")
    implementation("androidx.room:room-ktx:2.6.1")

    // Gson for JSON serialization
    implementation("com.google.code.gson:gson:2.10.1")

    // Work Manager for background tasks
    implementation("androidx.work:work-runtime-ktx:2.9.0")
    
    // MapLibre GL for OpenStreetMap display
    implementation("org.maplibre.gl:android-sdk:11.5.0")
    implementation("org.slf4j:slf4j-nop:1.7.36")

    // -----------------------------------------------------------------------
    // Firebase – use the BoM to keep all Firebase library versions in sync
    // -----------------------------------------------------------------------
    // implementation(platform("com.google.firebase:firebase-bom:33.1.0"))
    // Analytics – understand user flows and feature usage
    // implementation("com.google.firebase:firebase-analytics-ktx")
    // Crashlytics – automatic crash and ANR reporting with de-obfuscated traces
    // implementation("com.google.firebase:firebase-crashlytics-ktx")
    // Performance Monitoring – network request and screen rendering metrics
    // implementation("com.google.firebase:firebase-perf-ktx")

    // -----------------------------------------------------------------------
    // Testing
    // -----------------------------------------------------------------------
    testImplementation("junit:junit:4.13.2")
    // Robolectric – run Android unit tests on the JVM (no emulator needed for
    // logic-heavy unit tests; use Firebase Test Lab for full UI test matrix)
    testImplementation("org.robolectric:robolectric:4.12.1")
    androidTestImplementation("androidx.test.ext:junit:1.1.5")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.5.1")
    // Firebase Test Lab uses the standard instrumented test APK – no extra dep
}
