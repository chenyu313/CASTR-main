import torch
import math
import sys
import torch.nn as nn


def gelu(x):
    """Implementation of the gelu activation function.
        For information: OpenAI GPT's gelu is slightly different (and gives slightly different results):
        0.5 * x * (1 + torch.tanh(math.sqrt(2 / math.pi) * (x + 0.044715 * torch.pow(x, 3))))
        Also see https://arxiv.org/abs/1606.08415
    """
    return x * 0.5 * (1.0 + torch.erf(x / math.sqrt(2.0)))


class GeLU(nn.Module):
    """Implementation of the gelu activation function.
        For information: OpenAI GPT's gelu is slightly different (and gives slightly different results):
        0.5 * x * (1 + torch.tanh(math.sqrt(2 / math.pi) * (x + 0.044715 * torch.pow(x, 3))))
        Also see https://arxiv.org/abs/1606.08415
    """
    def __init__(self):
        super().__init__()

    def forward(self, x):
        return gelu(x)


def swish(x):
    return x * torch.sigmoid(x)

ACT2FN = {"gelu": gelu, "relu": torch.nn.functional.relu, "swish": swish}
BertLayerNorm = torch.nn.LayerNorm

class BertAttention(nn.Module):
    def __init__(self, config, ctx_dim=None):
        super().__init__()
        if config.hidden_size % config.num_attention_heads != 0:
            raise ValueError(
                "The hidden size (%d) is not a multiple of the number of attention "
                "heads (%d)" % (config.hidden_size, config.num_attention_heads))
        self.num_attention_heads = config.num_attention_heads
        self.attention_head_size = int(config.hidden_size / config.num_attention_heads)
        self.all_head_size = self.num_attention_heads * self.attention_head_size

        # cross_dim = 2048
        if ctx_dim is None:
            ctx_dim =config.hidden_size
        self.query = nn.Linear(config.hidden_size, self.all_head_size)
        self.key = nn.Linear(ctx_dim, self.all_head_size)
        self.value = nn.Linear(ctx_dim, self.all_head_size)

        self.dropout = nn.Dropout(config.attention_probs_dropout_prob)

    def transpose_for_scores(self, x):
        new_x_shape = x.size()[:-1] + (self.num_attention_heads, self.attention_head_size)
        x = x.view(*new_x_shape)
        return x.permute(0, 2, 1, 3)

    def forward(self, hidden_states, context, attention_mask=None):
        mixed_query_layer = self.query(hidden_states)
        mixed_key_layer = self.key(context)
        mixed_value_layer = self.value(context)

        query_layer = self.transpose_for_scores(mixed_query_layer)
        key_layer = self.transpose_for_scores(mixed_key_layer)
        value_layer = self.transpose_for_scores(mixed_value_layer)

        # Take the dot product between "query" and "key" to get the raw attention scores.
        attention_scores = torch.matmul(query_layer, key_layer.transpose(-1, -2))
        attention_scores = attention_scores / math.sqrt(self.attention_head_size)
        # Apply the attention mask is (precomputed for all layers in BertModel forward() function)
        if attention_mask is not None:
            attention_scores = attention_scores + attention_mask

        # Normalize the attention scores to probabilities.
        attention_probs = nn.Softmax(dim=-1)(attention_scores)

        # This is actually dropping out entire tokens to attend to, which might
        # seem a bit unusual, but is taken from the original Transformer paper.
        attention_probs = self.dropout(attention_probs)

        context_layer = torch.matmul(attention_probs, value_layer)
        context_layer = context_layer.permute(0, 2, 1, 3).contiguous()
        new_context_layer_shape = context_layer.size()[:-2] + (self.all_head_size,)
        context_layer = context_layer.view(*new_context_layer_shape)
        return context_layer

class BertAttOutput(nn.Module):
    def __init__(self, config):
        super(BertAttOutput, self).__init__()
        self.dense = nn.Linear(config.hidden_size, config.hidden_size)
        self.LayerNorm = BertLayerNorm(config.hidden_size, eps=1e-12)
        self.dropout = nn.Dropout(config.hidden_dropout_prob)

    def forward(self, hidden_states, input_tensor):
        hidden_states = self.dense(hidden_states)
        hidden_states = self.dropout(hidden_states)
        hidden_states = self.LayerNorm(hidden_states + input_tensor)
        return hidden_states

class BertCrossattLayer(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.att = BertAttention(config)
        self.output = BertAttOutput(config)

    def forward(self, input_tensor, ctx_tensor, ctx_att_mask=None):
        output = self.att(input_tensor, ctx_tensor, ctx_att_mask)
        attention_output = self.output(output, input_tensor)
        return attention_output

class BertSelfattLayer(nn.Module):
    def __init__(self, config):
        super(BertSelfattLayer, self).__init__()
        self.self = BertAttention(config)
        self.output = BertAttOutput(config)

    def forward(self, input_tensor, attention_mask):
        # Self attention attends to itself, thus keys and querys are the same (input_tensor).
        self_output = self.self(input_tensor, input_tensor, attention_mask)
        attention_output = self.output(self_output, input_tensor)
        return attention_output


class BertIntermediate(nn.Module):
    def __init__(self, config):
        super(BertIntermediate, self).__init__()
        self.dense = nn.Linear(config.hidden_size, config.intermediate_size)
        if isinstance(config.hidden_act, str) or (sys.version_info[0] == 2 and isinstance(config.hidden_act, unicode)):
            self.intermediate_act_fn = ACT2FN[config.hidden_act]
        else:
            self.intermediate_act_fn = config.hidden_act

    def forward(self, hidden_states):
        hidden_states = self.dense(hidden_states)
        hidden_states = self.intermediate_act_fn(hidden_states)
        return hidden_states


class BertOutput(nn.Module):
    def __init__(self, config):
        super(BertOutput, self).__init__()
        self.dense = nn.Linear(config.intermediate_size, config.hidden_size)
        self.LayerNorm = BertLayerNorm(config.hidden_size, eps=1e-12)
        self.dropout = nn.Dropout(config.hidden_dropout_prob)

    def forward(self, hidden_states, input_tensor):
        hidden_states = self.dense(hidden_states)
        hidden_states = self.dropout(hidden_states)
        hidden_states = self.LayerNorm(hidden_states + input_tensor)
        return hidden_states

class BertLayer(nn.Module):
    def __init__(self, config):
        super(BertLayer, self).__init__()
        self.attention = BertSelfattLayer(config)
        self.intermediate = BertIntermediate(config)
        self.output = BertOutput(config)

    def forward(self, hidden_states, attention_mask):
        attention_output = self.attention(hidden_states, attention_mask)
        intermediate_output = self.intermediate(attention_output)
        layer_output = self.output(intermediate_output, attention_output)
        return layer_output

class BertPooler(nn.Module):
    def __init__(self, config):
        super(BertPooler, self).__init__()
        self.dense = nn.Linear(config.hidden_size, config.hidden_size)
        self.activation = nn.ReLU()

    def forward(self, hidden_states):
        # We "pool" the model by simply taking the hidden state corresponding
        # to the first token.
        first_token_tensor = hidden_states[:, 0]
        pooled_output = self.dense(first_token_tensor)
        pooled_output = self.activation(pooled_output)
        return pooled_output

class CrossLayer(nn.Module):
    def __init__(self, config):
        super().__init__()
        # The cross-attention Layer
        self.cross_attention = BertCrossattLayer(config)

        # Self-attention Layers
        self.text_self_att = BertSelfattLayer(config)
        self.structure_self_att = BertSelfattLayer(config)

        # Intermediate and Output Layers (FFNs)
        self.text_inter = BertIntermediate(config)
        self.text_output = BertOutput(config)
        self.structure_inter = BertIntermediate(config)
        self.structure_output = BertOutput(config)

    def cross_att(self, text_input, text_attention_mask, structure_input, structure_attention_mask):
        # Cross Attention
        text_att_output = self.cross_attention(text_input, structure_input, ctx_att_mask=structure_attention_mask)
        structure_att_output = self.cross_attention(structure_input, text_input, ctx_att_mask=text_attention_mask)
        return text_att_output, structure_att_output

    def self_att(self, text_input, text_attention_mask, structure_input, structure_attention_mask):
        # Self Attention
        text_att_output = self.text_self_att(text_input, text_attention_mask)
        structure_att_output = self.structure_self_att(structure_input, structure_attention_mask)
        return text_att_output, structure_att_output

    def output_fc(self, text_input, structure_input):
        # FC layers
        text_inter_output = self.text_inter(text_input)
        structure_inter_output = self.structure_inter(structure_input)

        # Layer output
        text_output = self.text_output(text_inter_output, text_input)
        structure_output = self.structure_output(structure_inter_output, structure_input)
        return text_output, structure_output

    def forward(self, text_feats, text_attention_mask,
                      structure_feats, structure_attention_mask):
        text_att_output = text_feats
        structure_att_output = structure_feats

        text_att_output, structure_att_output = self.cross_att(text_att_output, text_attention_mask,
                                                          structure_att_output, structure_attention_mask)
        text_att_output, structure_att_output = self.self_att(text_att_output, text_attention_mask,
                                                         structure_att_output, structure_attention_mask)
        text_output, structure_output = self.output_fc(text_att_output, structure_att_output)

        return text_output, structure_output

class StructureFeatEncoder(nn.Module):
    def __init__(self, config):
        super().__init__()
        feat_dim = 128

        # Object feature encoding
        self.structure_fc = nn.Linear(feat_dim, config.hidden_size)
        self.structure_layer_norm = BertLayerNorm(config.hidden_size, eps=1e-12)

        self.dropout = nn.Dropout(config.hidden_dropout_prob)

    def forward(self, structure_input):
        feats = structure_input

        x = self.structure_fc(feats)
        x = self.structure_layer_norm(x)
        output = x

        output = self.dropout(output)
        return output

class CrossEncoder(nn.Module):
    def __init__(self, config):
        super().__init__()

        # Obj-level image embedding layer
        self.structure_fc = StructureFeatEncoder(config)
        
        # Number of layers
        self.num_t_layers = 1
        self.num_x_layers = 1
        self.num_s_layers = 5
        print("Cross encoder with %d t_layers, %d x_layers, and %d s_layers." %
              (self.num_t_layers, self.num_x_layers, self.num_s_layers))

        # Layers
        # Using self.layer instead of self.l_layer to support loading BERT weights.
        self.layer = nn.ModuleList(
            [BertLayer(config) for _ in range(self.num_t_layers)]
        )
        self.x_layers = nn.ModuleList(
            [CrossLayer(config) for _ in range(self.num_x_layers)]
        )
        self.r_layers = nn.ModuleList(
            [BertLayer(config) for _ in range(self.num_s_layers)]
        )

    def forward(self, text_feats, text_attention_mask,
                structure_feats, structure_attention_mask=None):
        # Run visual embedding layer
        # Note: Word embedding layer was executed outside this module.
        #       Keep this design to allow loading BERT weights.
        structure_feats = self.structure_fc(structure_feats)
        
        # Run textuage layers
        for layer_module in self.layer:
            text_feats = layer_module(text_feats, text_attention_mask)

        # Run relational layers
        for layer_module in self.r_layers:
            structure_feats = layer_module(structure_feats, structure_attention_mask)

        # Run cross-modality layers
        for layer_module in self.x_layers:
            text_feats, structure_feats = layer_module(text_feats, text_attention_mask,
                                                  structure_feats, structure_attention_mask)

        return text_feats, structure_feats

class CrossModel(nn.Module):
    """Cross Model."""

    def __init__(self, config):
        super(CrossModel , self).__init__()
        self.encoder = CrossEncoder(config)
        self.pooler = BertPooler(config)

    def forward(self, text_input, text_attention_mask=None,
                r_structure_input=None, r_structure_attention_mask=None):
        if text_attention_mask is None:
            text_attention_mask = torch.ones_like(text_input)

        # We create a 3D attention mask from a 2D tensor mask.
        # Sizes are [batch_size, 1, 1, to_seq_length]
        # So we can broadcast to [batch_size, num_heads, from_seq_length, to_seq_length]
        # this attention mask is more simple than the triangular masking of causal attention
        # used in OpenAI GPT, we just need to prepare the broadcast dimension here.
        extended_text_attention_mask = text_attention_mask.unsqueeze(1).unsqueeze(2)

        # Since attention_mask is 1.0 for positions we want to attend and 0.0 for
        # masked positions, this operation will create a tensor which is 0.0 for
        # positions we want to attend and -10000.0 for masked positions.
        # Since we are adding it to the raw scores before the softmax, this is
        # effectively the same as removing these entirely.
        extended_text_attention_mask = extended_text_attention_mask.to(dtype=next(self.parameters()).dtype) # fp16 compatibility
        extended_text_attention_mask = (1.0 - extended_text_attention_mask) * -10000.0

        # Process the visual attention mask
        if r_structure_attention_mask is not None:
            extended_r_structure_attention_mask = r_structure_attention_mask.unsqueeze(1).unsqueeze(2)
            extended_r_structure_attention_mask = extended_r_structure_attention_mask.to(dtype=next(self.parameters()).dtype) # fp16 compatibility
            extended_r_structure_attention_mask = (1.0 - extended_r_structure_attention_mask) * -10000.0
        else:
            extended_r_structure_attention_mask = None

        # Run LXRT backbone
        text_feats, structure_feats = self.encoder(
            text_input,
            extended_text_attention_mask,
            structure_feats=r_structure_input,
            structure_attention_mask=extended_r_structure_attention_mask)
        pooled_output = self.pooler(text_feats)

        return (text_feats, structure_feats), pooled_output

class CrossConfig:
    def __init__(self):
        self.hidden_size = 768
        self.num_hidden_layers = 12
        self.num_attention_heads = 12
        self.intermediate_size = 3072
        self.hidden_act = "gelu"
        self.hidden_dropout_prob = 0
        self.attention_probs_dropout_prob = 0
        self.max_position_embeddings = 512
        self.type_vocab_size = 2
        self.initializer_range = 0.02
        self.vocab_size=32