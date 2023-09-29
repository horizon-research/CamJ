module sipo (
    input clr,
    input clk,
    input d,
    output reg [4:0] q
);
    reg [4:0] temp;
    always @(posedge clk) begin
        if (clr==1)
            q=5'b00000;
        else begin
            temp = q>>1;
            q={d,temp[3:0]};
        end
    end
endmodule