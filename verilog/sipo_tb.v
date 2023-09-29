module sipo_tb;

reg clr;
reg clk;
reg d;

wire [4:0] q;

sipo dut (
    .clr(clr),
    .clk(clk),
    .d(d),
    .q(q)
)

initial begin
    clr = 1;
    clk = 0;
    d = 0;
    #10 clk=1'b0;
end

always #1 clk=~clk;
always #2 d=~d;
initial $monitor("d=%b, q=%b",d,q);
initial #50 $finish;

endmodule