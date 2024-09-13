# path =r"C:\Users\Chanchal Juyal\Desktop\My Work\gol\Execution_3_U_7_2\DU_Logs\test.txt"
# file = open(path,'r')
# # file.write("Hello, World123!\n")

# for line in file:
#     print(line.strip())

#CSV file
import csv
path =r"C:\Users\Chanchal Juyal\Desktop\My Work\gol\Execution_3_U_7_2\DU_Logs\test.csv"
try:
    with open(path,'w') as file:
        writer = csv.writer(file)
        writer.writerow(["Name", "Age"])
        writer.writerow(["Alice", 30])
        writer.writerow(["Bob", 25])
except PermissionError as e:
    print("Error:", e)


