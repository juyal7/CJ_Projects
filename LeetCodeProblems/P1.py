

# def targetsum():
#     list=[]
#     for i in nums:
#         for j in nums:
#             if i+j==target:
#                 list.append(i)
#                 list.append(j)
#     return set(list)
# print(targetsum())
from typing import List

list = [2,7,11,15,5,4,6,3]
target=9
class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        d = {}  # Dictionary (hashmap) to store numbers and their indices
        result = []  # List to store all index pairs
        for i, x in enumerate(nums):  # Loop through the list
            if (y := target - x) in d:  # Check if the complement exists in the dictionary
                result.append([d[y], i])  # If found, return the stored index and the current index
            # d[x] = i  # Store the current number with its index
        return result

obj=Solution()
a=obj.twoSum(list,target)
print(a)    
            