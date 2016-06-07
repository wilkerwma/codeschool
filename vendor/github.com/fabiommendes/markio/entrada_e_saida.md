Entrada e saída (básico)
========================

    Author: Fábio Mendes
    Timeout: 1.0

Programa simples testando as operações de entrada e saída


Description
-----------

Quase sempre queremos que nossos programas interajam de alguma forma com o usuário. A maneira mais simples de interação talvez seja escrevendo e lendo valores digitados em um terminal. Vamos então começar com um programa bem simples: ele deve perguntar o nome e idade do usuário e mostrar uma mensagem na tela dizendo qual será a idade do mesmo daqui a 5 anos.

A esta tarefa simples, vamos adicionar uma dificuldade. Todas as mensagens trocadas entre o programa e o usuário devem seguir **exatamente** o modelo abaixo, reproduzindo cada ponto, cada letra maiúscula e até mesmo os espaços em branco:

    Nome: <entrada do usuário>
    Idade: <entrada do usuário>
    Oi <nome>, você terá <número> anos daqui a cinco anos!

É lógico que os campos <entrada do usuário>, <nome> e <número> devem ser substituídos pelos valores digitados durante a execução do programa.

O Codeschool simula um usuário humano interagindo com o seu programa e testa os resultados para verificar se os mesmos correspondem ao esperado. Geralmente cada programa é testado várias vezes com várias entradas diferinptentes. Agora é mãos à obra e boa programação!

Tests
-----

    Nome: <Maria>
    Idade: <20>
    Oi Maria, você terá 25 anos daqui a cinco anos!

    Nome: <Paulo>
    Idade: <0>
    Oi Paulo, você terá 5 anos daqui a cinco anos!

    Nome: <Albert Einstein>
    Idade: <70>
    Oi Albert Einstein, você terá 75 anos daqui a cinco anos!

    @input
        $name
        $int(0..100)


Answer Key (pytuga)
-------------------

    nome = leia_texto("Nome: ")
    idade = leia_número("Idade:")
    mostre("Oi %s, você terá %s anos daqui a cinco anos!" % (nome, idade + 5))
