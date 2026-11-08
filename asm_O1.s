	.file	"main.c"
	.option nopic
	.attribute arch, "rv32i2p1_m2p0_zmmul1p0"
	.attribute unaligned_access, 0
	.attribute stack_align, 16
	.text
	.align	2
	.globl	main
	.type	main, @function
main:
	addi	sp,sp,-64
	sw	s0,60(sp)
	sw	s1,56(sp)
	sw	s2,52(sp)
	sw	s3,48(sp)
	sw	s4,44(sp)
	sw	s5,40(sp)
	sw	s6,36(sp)
	sw	s7,32(sp)
	sw	s8,28(sp)
	sw	s9,24(sp)
	sw	s10,20(sp)
	sw	s11,16(sp)
	lui	a6,%hi(.LANCHOR0)
	addi	a6,a6,%lo(.LANCHOR0)
	lw	t0,0(a6)
	lui	a5,%hi(pass_count)
	lw	t6,%lo(pass_count)(a5)
	lw	s10,16(a6)
	lw	s9,12(a6)
	lw	s7,8(a6)
	lw	s3,4(a6)
	addi	a3,a6,20
	addi	a6,a6,188
	mv	a2,a3
	sw	zero,12(sp)
	sw	zero,8(sp)
	sw	zero,4(sp)
	li	s6,0
	li	s2,0
	li	s1,0
	li	a7,0
	li	a4,1228800
	addi	a4,a4,1218
	li	t5,1662976
	addi	t5,t5,1549
	li	t4,1013903360
	addi	t4,t4,863
	li	t3,1148157952
	addi	t3,t3,1623
	li	s0,101
	li	t2,57
	li	s5,49
	li	t1,1
	li	s4,64
	li	s8,74
	li	s11,84
	j	.L8
.L19:
	mv	s1,t1
.L3:
	addi	s3,s3,1
	mv	s6,t1
	j	.L5
.L6:
	bgt	a5,s11,.L7
	addi	s9,s9,1
	sw	t1,8(sp)
	mv	s1,t1
	j	.L5
.L7:
	addi	s10,s10,1
	sw	t1,12(sp)
	mv	s1,t1
	j	.L5
.L27:
	lw	a5,12(sp)
	beq	a5,zero,.L9
	lui	a5,%hi(.LANCHOR0+16)
	sw	s10,%lo(.LANCHOR0+16)(a5)
.L9:
	lw	a5,8(sp)
	beq	a5,zero,.L10
	lui	a5,%hi(.LANCHOR0+12)
	sw	s9,%lo(.LANCHOR0+12)(a5)
.L10:
	lw	a5,4(sp)
	beq	a5,zero,.L11
	lui	a5,%hi(.LANCHOR0+8)
	sw	s7,%lo(.LANCHOR0+8)(a5)
.L11:
	beq	s6,zero,.L12
	lui	a5,%hi(.LANCHOR0+4)
	sw	s3,%lo(.LANCHOR0+4)(a5)
.L12:
	beq	s2,zero,.L13
	lui	a5,%hi(.LANCHOR0)
	sw	t0,%lo(.LANCHOR0)(a5)
.L13:
	beq	s1,zero,.L14
	lui	a5,%hi(pass_count)
	sw	t6,%lo(pass_count)(a5)
.L14:
	li	a1,818089984
	addi	a1,a1,-975
	mulh	a1,a7,a1
	srai	a1,a1,3
	srai	a7,a7,31
	sub	a1,a1,a7
	lui	a5,%hi(mean)
	sw	a1,%lo(mean)(a5)
	lui	a5,%hi(below_count)
	lw	a2,%lo(below_count)(a5)
	li	a0,0
	li	a7,1
	j	.L16
.L26:
	ori	a4,a5,256
	beq	a5,a4,.L15
	sw	a4,0(a3)
	addi	a2,a2,1
	mv	a0,a7
.L15:
	addi	a3,a3,4
	beq	a6,a3,.L25
.L16:
	lw	a5,0(a3)
	ble	a1,a5,.L15
	j	.L26
.L25:
	beq	a0,zero,.L20
	lui	a5,%hi(below_count)
	sw	a2,%lo(below_count)(a5)
.L20:
	li	a0,0
	lw	s0,60(sp)
	lw	s1,56(sp)
	lw	s2,52(sp)
	lw	s3,48(sp)
	lw	s4,44(sp)
	lw	s5,40(sp)
	lw	s6,36(sp)
	lw	s7,32(sp)
	lw	s8,28(sp)
	lw	s9,24(sp)
	lw	s10,20(sp)
	lw	s11,16(sp)
	addi	sp,sp,64
	jr	ra
.L2:
	bgt	a5,s5,.L3
	addi	t0,t0,1
	mv	s2,t1
.L5:
	addi	a2,a2,4
	beq	a6,a2,.L27
.L8:
	mul	a4,a4,t5
	add	a4,a4,t4
	srli	a1,a4,16
	mulhu	a5,a1,t3
	sub	a0,a1,a5
	srli	a0,a0,1
	add	a5,a5,a0
	srli	a5,a5,6
	mul	a5,a5,s0
	sub	a5,a1,a5
	sw	a5,0(a2)
	add	a7,a7,a5
	ble	a5,t2,.L2
	addi	t6,t6,1
	ble	a5,s4,.L19
	bgt	a5,s8,.L6
	addi	s7,s7,1
	sw	t1,4(sp)
	mv	s1,t1
	j	.L5
	.size	main, .-main
	.align	2
	.globl	mark_below
	.type	mark_below, @function
mark_below:
	blt	a0,a1,.L30
.L29:
	ret
.L30:
	ori	a0,a0,256
	ret
	.size	mark_below, .-mark_below
	.globl	pass_count
	.globl	below_count
	.globl	mean
	.globl	bucket
	.globl	grades
	.globl	SID
	.bss
	.align	2
	.set	.LANCHOR0,. + 0
	.type	bucket, @object
	.size	bucket, 20
bucket:
	.zero	20
	.type	grades, @object
	.size	grades, 168
grades:
	.zero	168
	.section	.sbss,"aw",@nobits
	.align	2
	.type	pass_count, @object
	.size	pass_count, 4
pass_count:
	.zero	4
	.type	below_count, @object
	.size	below_count, 4
below_count:
	.zero	4
	.type	mean, @object
	.size	mean, 4
mean:
	.zero	4
	.section	.srodata,"a"
	.align	2
	.type	SID, @object
	.size	SID, 4
SID:
	.word	1230018
	.ident	"GCC: (xPack GNU RISC-V Embedded GCC x86_64) 15.2.0"
	.section	.note.GNU-stack,"",@progbits
