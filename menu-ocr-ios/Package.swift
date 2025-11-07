// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "MenuOCR",
    platforms: [
        .iOS(.v15)
    ],
    products: [
        .library(
            name: "MenuOCR",
            targets: ["MenuOCR"]
        ),
    ],
    dependencies: [
        .package(url: "https://github.com/supabase-community/supabase-swift.git", from: "2.0.0"),
    ],
    targets: [
        .target(
            name: "MenuOCR",
            dependencies: [
                .product(name: "Supabase", package: "supabase-swift"),
            ],
            path: "MenuOCR/MenuOCR"
        ),
    ]
)