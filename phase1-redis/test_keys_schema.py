from keys import RedisSchema


def test_keys():
    print("--- Verifying RedisSchema ---")

    # Test Trip Keys
    trip_id = "TRIP-ABC-123"
    context_key = RedisSchema.Trip.context(trip_id)
    print(f"Trip Context Key: {context_key}")
    assert context_key == f"trip:{trip_id}:context"
    print(f"Trip Context TTL: {RedisSchema.Trip.CONTEXT_TTL}s")

    output_key = RedisSchema.Trip.output(trip_id, "safety")
    print(f"Trip Output Key: {output_key}")
    assert output_key == f"trip:{trip_id}:concierge_output"

    # Test Driver Keys
    driver_id = "DRV-99"
    driver_key = RedisSchema.Driver.profile(driver_id)
    print(f"Driver Profile Key: {driver_key}")
    assert driver_key == f"driver:{driver_id}:profile"
    print(f"Driver Profile TTL: {RedisSchema.Driver.PROFILE_TTL}s")

    # Test Telemetry Keys
    device_id = "IOT-X1"
    telemetry_key = RedisSchema.Telemetry.buffer(device_id)
    print(f"Telemetry Buffer Key: {telemetry_key}")
    assert telemetry_key == f"telemetry:{device_id}:buffer"

    print("\n✅ Verification Successful: All keys and TTLs match expected patterns.")


if __name__ == "__main__":
    try:
        test_keys()
    except Exception as e:
        print(f"❌ Verification Failed: {e}")
