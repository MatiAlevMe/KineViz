import numpy as np
import spm1d
import matplotlib.pyplot as plt

# Generar datos aleatorios para tres grupos (J_k x Q)
np.random.seed(42)  # Fijar la semilla para reproducibilidad
Y1 = np.random.normal(loc=50, scale=5, size=(10, 100))  # Grupo 1
Y2 = np.random.normal(loc=55, scale=5, size=(10, 100))  # Grupo 2
Y3 = np.random.normal(loc=60, scale=5, size=(10, 100))  # Grupo 3

# Realizar ANOVA de una vía
F = spm1d.stats.anova1([Y1, Y2, Y3], equal_var=False)
Fi = F.inference(alpha=0.05, interp=True)