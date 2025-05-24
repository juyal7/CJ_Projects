class Solution:
    def twoSum(self, nums, target):
        ans = []
        for i in range(len(nums)):
            for j in range(i + 1, len(nums)):  # Avoid i == j and redundant checks
                if nums[i] + nums[j] == target:
                    ans.append((i,j))
        return ans  # Return immediately if solution found
        # return []  # Return empty if no solution found

obj1 = Solution()
a = obj1.twoSum([1, 2, 3, 4, 5,7], 9)
print(a)  # Output: [3, 4] (indices of elements that sum to 9)