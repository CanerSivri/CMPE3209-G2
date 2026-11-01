/* Caner Sivri, 5001230018, G2 - Exam Grade Distribution*/
#define N 42 // compile time constant

const int SID = 1230018; // last 9 digits since my complete SID exceeds 2^32
int grades[N]; // global array (N defined compile time constant therefore we able to declare array as global array)
int bucket[5];
int mean = 0;
int below_count = 0;
int pass_count = 0;
int mark_below(int note, int avg);

int main(void){
    unsigned int x = (unsigned int)SID;
    int pass_limit = 50 + (SID % 10); // Calculated within guideline's instructions using my SID (last digit of SID)
    int sum = 0;

    for(int i=0;i<N;i++){
        x = 1664525U * x + 1013904223U; // random number generator (LCG)
        int v = (int)(((x >> 16) % 101U) + 0U); // keeps the upper 16 bits to turn x into an integer grade (because LCG is bad at being random in the low bits)
        grades[i] = v;
        sum += v;

        if(v >= pass_limit){
            pass_count++;
        }
        if(v < 50){
            bucket[0]++;
        }
        else if(v < 65){
            bucket[1]++;
        }
        else if(v < 75){
            bucket[2]++;
        }
        else if(v < 85){
            bucket [3]++;
        }
        else{
            bucket[4]++;
        }
    }

    mean = sum / N;

    for(int i=0;i<N;i++){
        int marked = mark_below(grades[i],mean);
        if(marked != grades[i]){
            grades[i] = marked;
            below_count++;
        }
    }
    return 0;
}

int mark_below(int note, int avg){
    if (note < avg){
        return note | 0x100; // sets bit 8 as a "below average" flag inside the same integer without losing the grade
    }
    return note;
}