def calculate_risk(metadata, forensic_data, watermark_result):

    authenticity = 100
    breakdown = []

    width = forensic_data["width"]
    height = forensic_data["height"]
    edge_density = forensic_data["edge_density"]
    entropy = forensic_data["entropy"]

    # -------- METADATA CHECK --------
    if not metadata:
        authenticity -= 20
        breakdown.append({
            "title": "Missing Metadata",
            "impact_score": 20,
            "analysis": f"No EXIF metadata detected. Authentic camera images typically contain device make, model and timestamp.",
            "risk_reason": "Absence of metadata reduces traceability and origin validation."
        })
    else:
        breakdown.append({
            "title": "Metadata Verified",
            "impact_score": 0,
            "analysis": "EXIF metadata detected. Device-origin traceability available.",
            "risk_reason": "Metadata presence supports authenticity verification."
        })

    # -------- RESOLUTION CHECK --------
    if width < 500 or height < 500:
        authenticity -= 10
        breakdown.append({
            "title": "Low Resolution Image",
            "impact_score": 10,
            "analysis": f"Resolution detected: {width}x{height}. Low resolution may indicate screenshot or compression.",
            "risk_reason": "Low resolution images often result from editing or multiple compressions."
        })
    else:
        breakdown.append({
            "title": "High Resolution Integrity",
            "impact_score": 0,
            "analysis": f"Resolution detected: {width}x{height}. Suitable for original capture.",
            "risk_reason": "High resolution supports natural camera capture."
        })

    # -------- EDGE DENSITY --------
    if edge_density > 0.20:
        authenticity -= 15
        breakdown.append({
            "title": "High Edge Density Detected",
            "impact_score": 15,
            "analysis": f"Edge density value: {edge_density}. Sharp transitions detected.",
            "risk_reason": "High edge concentration may indicate digital recomposition or overlay."
        })
    elif edge_density < 0.05:
        authenticity -= 10
        breakdown.append({
            "title": "Unusually Smooth Structure",
            "impact_score": 10,
            "analysis": f"Edge density value: {edge_density}. Low structural variance.",
            "risk_reason": "Artificially generated graphics often have smoother regions."
        })
    else:
        breakdown.append({
            "title": "Normal Edge Distribution",
            "impact_score": 0,
            "analysis": f"Edge density value: {edge_density}. Within natural range.",
            "risk_reason": "Edge variation consistent with organic imagery."
        })

    # -------- ENTROPY CHECK --------
    if entropy < 4:
        authenticity -= 15
        breakdown.append({
            "title": "Low Entropy Pattern",
            "impact_score": 15,
            "analysis": f"Entropy score: {entropy}. Low pixel randomness.",
            "risk_reason": "Edited or compressed regions reduce natural pixel randomness."
        })
    elif entropy > 7:
        authenticity -= 10
        breakdown.append({
            "title": "Unusual High Entropy",
            "impact_score": 10,
            "analysis": f"Entropy score: {entropy}. Extremely high randomness.",
            "risk_reason": "May indicate noise injection or digital tampering."
        })
    else:
        breakdown.append({
            "title": "Healthy Entropy Level",
            "impact_score": 0,
            "analysis": f"Entropy score: {entropy}. Natural distribution.",
            "risk_reason": "Pixel randomness consistent with authentic imagery."
        })

    # -------- WATERMARK CHECK --------
    if watermark_result.get("watermark_detected"):
        authenticity -= 25
        breakdown.append({
            "title": "Watermark Presence",
            "impact_score": 25,
            "analysis": "Visible watermark pattern detected.",
            "risk_reason": "Watermarks may indicate reposted or redistributed media."
        })
    else:
        breakdown.append({
            "title": "No Watermark Found",
            "impact_score": 0,
            "analysis": "No watermark patterns detected.",
            "risk_reason": "Absence of watermark strengthens originality confidence."
        })

    # -------- SUSPICIOUS REGION --------
    if forensic_data.get("suspicious_region"):
        authenticity -= 15
        breakdown.append({
            "title": "Suspicious Region Highlighted",
            "impact_score": 15,
            "analysis": "Localized structural irregularity detected in image region.",
            "risk_reason": "Regional pixel inconsistency may indicate localized editing."
        })

    # Clamp
    if authenticity < 0:
        authenticity = 0

    # Tamper Level
    if authenticity > 75:
        tamper_level = "LOW"
    elif authenticity > 40:
        tamper_level = "MEDIUM"
    else:
        tamper_level = "HIGH"

    return authenticity, tamper_level, breakdown