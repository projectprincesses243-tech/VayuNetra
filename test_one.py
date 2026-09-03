from fusion import detect

image_path = "Perception/dataset/Fire/fire_image0001_0.png"

result = detect(image_path)

print("\n========== PERCEPTION OUTPUT ==========")
print("Image:", result["frame"])

if len(result["boxes"]) > 0:
    print("Survivor detected")
    print("Bounding boxes:", result["boxes"])
else:
    print("No survivor detected")

print("\n---------- CONFIDENCES ----------")
print("RGB confidence:", result["rgb_conf"])
print("Thermal confidence:", result["thermal_conf"])
print("Blob confidence:", result["blob_conf"])

print("\n---------- THRESHOLD RESULTS ----------")
print("RGB passed:", result["rgb_pass"])
print("Thermal passed:", result["thermal_pass"])
print("Blob passed:", result["blob_pass"])
print("Passed methods:", result["passed_methods"], "/ 3")

print("\n---------- FUSION RESULT ----------")
print("RGB weight: 0.50")
print("Thermal weight: 0.30")
print("Blob weight: 0.20")
print("Fusion score:", result["fusion_score"])

print("\n---------- FINAL DECISION ----------")
print("Decision:", result["decision"])
print("Alert:", result["alert"])

print("\n======================================")