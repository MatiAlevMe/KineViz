import numpy as np
import spm1d
import traceback

print(f"spm1d version: {spm1d.__version__}")
print(f"numpy version: {np.__version__}")

Y0 = np.random.rand(1, 101).reshape(1, -1)
print(Y0)
Y1 = np.random.rand(1, 101).reshape(1, -1)
print (Y1)
Y2 = np.random.rand(1, 101).reshape(1, -1)

print("Attempting spm1d.stats.anova1...")
try:
    alpha = spm1d.stats.anova1((Y0, Y1,Y2), equal_var=False)
    print("spm1d.stats.anova1 call successful.")
    # Perform inference if the call was successful
    # inference_result = alpha.inference(0.05)
    # print(inference_result)
except Exception as e:
    print(f"Error in minimal spm1d.stats.anova1 example: {e}")
    traceback.print_exc()