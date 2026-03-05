import Foundation

/// Configuration for retry behavior
struct RetryConfig {
    let enabled: Bool
    let delaySeconds: TimeInterval
    let maxAttempts: Int
    let backoffMultiplier: Double
    
    /// Default retry configuration matching Kilocode config
    static let `default` = RetryConfig(
        enabled: true,
        delaySeconds: 10,
        maxAttempts: 3,
        backoffMultiplier: 1.0
    )
}

/// Retry helper for handling transient failures with configurable retry logic
class RetryHelper {
    
    /// Retry an async function with exponential backoff
    /// - Parameters:
    ///   - config: Retry configuration (uses default if nil)
    ///   - operation: The async operation to retry
    /// - Returns: The result of the operation
    /// - Throws: The last error if all retries fail
    static func retry<T>(
        config: RetryConfig = .default,
        operation: @escaping () async throws -> T
    ) async throws -> T {
        guard config.enabled else {
            return try await operation()
        }
        
        var lastError: Error?
        var currentDelay = config.delaySeconds
        
        for attempt in 1...config.maxAttempts {
            do {
                #if DEBUG
                print("RetryHelper: Attempt \(attempt)/\(config.maxAttempts)")
                #endif
                let result = try await operation()
                if attempt > 1 {
                    #if DEBUG
                    print("RetryHelper: Successfully executed on attempt \(attempt)")
                    #endif
                }
                return result
            } catch {
                lastError = error
                #if DEBUG
                print("RetryHelper: Attempt \(attempt)/\(config.maxAttempts) failed: \(error.localizedDescription)")
                #endif
                
                if attempt < config.maxAttempts {
                    #if DEBUG
                    print("RetryHelper: Retrying in \(currentDelay) seconds...")
                    #endif
                    try await Task.sleep(nanoseconds: UInt64(currentDelay * 1_000_000_000))
                    currentDelay *= config.backoffMultiplier
                } else {
                    #if DEBUG
                    print("RetryHelper: All \(config.maxAttempts) attempts failed")
                    #endif
                }
            }
        }
        
        throw lastError ?? NSError(
            domain: "RetryHelper",
            code: -1,
            userInfo: [NSLocalizedDescriptionKey: "Retry failed with unknown error"]
        )
    }
    
    /// Retry a synchronous function with exponential backoff
    /// - Parameters:
    ///   - config: Retry configuration (uses default if nil)
    ///   - operation: The operation to retry
    /// - Returns: The result of the operation
    /// - Throws: The last error if all retries fail
    static func retrySync<T>(
        config: RetryConfig = .default,
        operation: () throws -> T
    ) throws -> T {
        guard config.enabled else {
            return try operation()
        }
        
        var lastError: Error?
        var currentDelay = config.delaySeconds
        
        for attempt in 1...config.maxAttempts {
            do {
                #if DEBUG
                print("RetryHelper: Attempt \(attempt)/\(config.maxAttempts)")
                #endif
                let result = try operation()
                if attempt > 1 {
                    #if DEBUG
                    print("RetryHelper: Successfully executed on attempt \(attempt)")
                    #endif
                }
                return result
            } catch {
                lastError = error
                #if DEBUG
                print("RetryHelper: Attempt \(attempt)/\(config.maxAttempts) failed: \(error.localizedDescription)")
                #endif
                
                if attempt < config.maxAttempts {
                    #if DEBUG
                    print("RetryHelper: Retrying in \(currentDelay) seconds...")
                    #endif
                    Thread.sleep(forTimeInterval: currentDelay)
                    currentDelay *= config.backoffMultiplier
                } else {
                    #if DEBUG
                    print("RetryHelper: All \(config.maxAttempts) attempts failed")
                    #endif
                }
            }
        }
        
        throw lastError ?? NSError(
            domain: "RetryHelper",
            code: -1,
            userInfo: [NSLocalizedDescriptionKey: "Retry failed with unknown error"]
        )
    }
}
