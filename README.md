#include<stdio.h>
int middle_element(int);
int main()
    {
        int a[100],b,c,i;
    printf("please enetr the no. of digits your wants to enetr=");
    scanf("%d",&b);
    for(i=0;i<b;i++)
        {
            printf("please enter [%d]th element of array=",i);
            scanf("%d",&a[i]);
        }
    for(i=0;i<b;i++)
        {
            printf("[%d]th element of array is=%d\n",i,a[i]);
        }
    c=middle_element(b);
    printf("middle element is [%d]th value is = %d ",c,a[c]);
    }
int middle_element(int n)
    {
        int m;
        if (n%2==0)
            {
            m=n/2;
            return(m);
            }
        else
            {
                m=((n+1)/2);
                return(m);
            }
    }
