basic_ledger = """
WITH Razao_Geral AS (
    SELECT 
        lancto.fili_lan AS FILIAL, 
        lancto.data_lan AS DATA, 
        lancto.cdeb_lan AS DEBITO, 
        lancto.ccre_lan AS CREDITO, 
        lancto.chis_lan AS HISTORICO, 
        lancto.vlor_lan AS VALOR
    FROM 
        bethadba.ctlancto lancto
    LEFT JOIN 
        bethadba.ctcontas contas ON lancto.codi_emp = contas.codi_emp AND lancto.cdeb_lan = contas.codi_cta
    WHERE 
        lancto.fili_lan IN (?)
        AND lancto.data_lan BETWEEN CONVERT(DATE, ?, 103) AND CONVERT(DATE, ?, 103)
        AND contas.codi_cta = ?
    
    UNION ALL 

    SELECT 
        lancto.fili_lan, 
        lancto.data_lan, 
        lancto.cdeb_lan, 
        lancto.ccre_lan, 
        lancto.chis_lan, 
        (lancto.vlor_lan * -1) AS VALOR
    FROM 
        bethadba.ctlancto lancto
    LEFT JOIN 
        bethadba.ctcontas contas ON lancto.codi_emp = contas.codi_emp AND lancto.ccre_lan = contas.codi_cta
    WHERE 
        lancto.fili_lan IN (?) 
        AND lancto.data_lan BETWEEN CONVERT(DATE, ?, 103) AND CONVERT(DATE, ?, 103)
        AND contas.codi_cta = ?
)
SELECT * FROM Razao_Geral 
ORDER BY FILIAL, DATA;
"""

general_ledger = """
WITH Razao_Geral AS (
    SELECT 
        lancto.fili_lan AS FILIAL, 
        lancto.data_lan AS DATA, 
        lancto.cdeb_lan AS DEBITO, 
        lancto.ccre_lan AS CREDITO, 
        REPLACE(lancto.chis_lan, CHAR(2), '') AS HISTORICO, 
        lancto.vlor_lan AS VALOR
    FROM 
        bethadba.ctlancto lancto
    LEFT JOIN 
        bethadba.ctcontas contas ON lancto.codi_emp = contas.codi_emp AND lancto.cdeb_lan = contas.codi_cta
    WHERE 
        lancto.fili_lan IN (?)
        AND lancto.data_lan BETWEEN CONVERT(DATE, ?, 103) AND CONVERT(DATE, ?, 103)
        AND contas.codi_cta LIKE (?)
    
    UNION ALL 

    SELECT 
        lancto.fili_lan, 
        lancto.data_lan, 
        lancto.cdeb_lan, 
        lancto.ccre_lan, 
        REPLACE(lancto.chis_lan, CHAR(2), '') AS HISTORICO, 
        (lancto.vlor_lan * -1) AS VALOR
    FROM 
        bethadba.ctlancto lancto
    LEFT JOIN 
        bethadba.ctcontas contas ON lancto.codi_emp = contas.codi_emp AND lancto.ccre_lan = contas.codi_cta
    WHERE 
        lancto.fili_lan IN (?)
        AND lancto.data_lan BETWEEN CONVERT(DATE, ?, 103) AND CONVERT(DATE, ?, 103)
        AND contas.codi_cta LIKE (?)
)
SELECT * FROM Razao_Geral 
ORDER BY FILIAL, DATA;
"""

get_client = """
    SELECT razao_emp, codi_emp
    FROM bethadba.geempre
    WHERE (stat_emp <> 'I') 
    AND (codi_emp IS NOT NULL) 
    AND LOWER(razao_emp) LIKE LOWER(?)
    """

get_balance = """
WITH SALDO_ANT_DEB AS (
    SELECT SUM(lancto.vlor_lan) AS Soma
    FROM bethadba.ctlancto lancto
    LEFT JOIN bethadba.ctcontas contas ON lancto.codi_emp = contas.codi_emp AND lancto.cdeb_lan = contas.codi_cta
    WHERE lancto.codi_emp IN (?)
    AND lancto.data_lan <= DATEADD(MONTH, -1, CONVERT(DATE, ?, 103))
    AND contas.codi_cta = ?
), 
SALDO_ANT_CRED AS (
    SELECT SUM(lancto.vlor_lan) AS Soma
    FROM bethadba.ctlancto lancto
    LEFT JOIN bethadba.ctcontas contas ON lancto.codi_emp = contas.codi_emp AND lancto.ccre_lan = contas.codi_cta
    WHERE lancto.codi_emp IN (?)
    AND lancto.data_lan <= DATEADD(MONTH, -1, CONVERT(DATE, ?, 103))
    AND contas.codi_cta = ?
)
SELECT (SELECT Soma FROM SALDO_ANT_CRED) - (SELECT Soma FROM SALDO_ANT_DEB) AS [SALDO ANTERIOR];
"""

get_balance_by_account_type = """
WITH SALDO_ANT_DEB AS (
    SELECT SUM(lancto.vlor_lan) AS Soma
    FROM bethadba.ctlancto lancto
    LEFT JOIN bethadba.ctcontas contas ON lancto.codi_emp = contas.codi_emp AND lancto.cdeb_lan = contas.codi_cta
    WHERE lancto.fili_lan IN (?)
    AND lancto.data_lan <= DATEADD(MONTH, -1, CONVERT(DATE, ?, 103))
    AND contas.codi_cta LIKE(? || '%')
), 
SALDO_ANT_CRED AS (
    SELECT SUM(lancto.vlor_lan) AS Soma
    FROM bethadba.ctlancto lancto
    LEFT JOIN bethadba.ctcontas contas ON lancto.codi_emp = contas.codi_emp AND lancto.ccre_lan = contas.codi_cta
    WHERE lancto.fili_lan IN (?)
    AND lancto.data_lan <= DATEADD(MONTH, -1, CONVERT(DATE, ?, 103))
    AND contas.codi_cta LIKE(? || '%')
)
SELECT (SELECT Soma FROM SALDO_ANT_CRED) - (SELECT Soma FROM SALDO_ANT_DEB) AS [SALDO ANTERIOR];
"""

# enterprises_suppliers = """
# select 
#     empresas.codi_emp codigo_empresa, 
#     empresas.apel_emp apelido_empresa, 
#     empresas.razao_emp razão_empresa, 
#     empresas.cgce_emp cnpj_cpf_empresa, 
#     fornecedores.codi_for código_fornecedor, 
#     fornecedores.nome_for nome_fornecedor, 
#     fornecedores.cgce_for cnpj_cpf_fornecedor
# from bethadba.geempre empresas
# left join bethadba.effornece fornecedores
# where empresas.stat_emp = 'A'
# and (fornecedores.cgce_for <> '' or fornecedores.cgce_for <> null)
# and empresas.codi_emp = fornecedores.codi_emp
# order by codigo_empresa, nome_fornecedor
# """
enterprises_suppliers = """
WITH Fornecedores AS (
    SELECT 
        empresas.codi_emp AS codigo_empresa, 
        empresas.apel_emp AS apelido_empresa, 
        empresas.razao_emp AS razao_empresa, 
        empresas.cgce_emp AS cnpj_cpf_empresa, 
        fornecedores.codi_for AS codigo_fornecedor, 
        fornecedores.nome_for AS nome_fornecedor, 
        fornecedores.cgce_for AS cnpj_cpf_fornecedor
    FROM bethadba.geempre empresas
    INNER JOIN bethadba.effornece fornecedores
        ON empresas.codi_emp = fornecedores.codi_emp
    WHERE empresas.stat_emp = 'A'
        AND (fornecedores.cgce_for <> '' AND fornecedores.cgce_for IS NOT NULL)
    
    UNION ALL 

    SELECT 
        empresas.codi_emp AS codigo_empresa, 
        empresas.apel_emp AS apelido_empresa, 
        empresas.razao_emp AS razao_empresa, 
        empresas.cgce_emp AS cnpj_cpf_empresa, 
        fornecedores.codi_for AS codigo_fornecedor, 
        fornecedores.nomr_for AS nome_fornecedor, 
        fornecedores.cgce_for AS cnpj_cpf_fornecedor
    FROM bethadba.geempre empresas
    INNER JOIN bethadba.effornece fornecedores
        ON empresas.codi_emp = fornecedores.codi_emp
    WHERE empresas.stat_emp = 'A'
        AND (fornecedores.cgce_for <> '' AND fornecedores.cgce_for IS NOT NULL)
)
SELECT DISTINCT
    codigo_empresa, 
    apelido_empresa, 
    razao_empresa, 
    cnpj_cpf_empresa, 
    codigo_fornecedor, 
    nome_fornecedor, 
    cnpj_cpf_fornecedor
FROM Fornecedores
ORDER BY codigo_empresa, nome_fornecedor
"""

search_historic = """
WITH Busca_historico AS (
    SELECT 
        lancto.fili_lan AS FILIAL, 
        lancto.data_lan AS DATA, 
        lancto.cdeb_lan AS DEBITO, 
        lancto.ccre_lan AS CREDITO, 
        lancto.chis_lan AS HISTORICO, 
        lancto.vlor_lan AS VALOR,
        CASE ?
            ELSE 0 
        END AS NUMERO
    FROM 
        bethadba.ctlancto lancto
    LEFT JOIN 
        bethadba.ctcontas contas ON lancto.codi_emp = contas.codi_emp AND lancto.cdeb_lan = contas.codi_cta
    WHERE 
        contas.codi_cta = ?

    UNION ALL 

    SELECT 
        lancto.fili_lan, 
        lancto.data_lan, 
        lancto.cdeb_lan, 
        lancto.ccre_lan, 
        lancto.chis_lan, 
        (lancto.vlor_lan * -1) AS VALOR,
        CASE ?
            ELSE 0 
        END AS NUMERO
    FROM 
        bethadba.ctlancto lancto
    LEFT JOIN 
        bethadba.ctcontas contas ON lancto.codi_emp = contas.codi_emp AND lancto.ccre_lan = contas.codi_cta
    WHERE 
        contas.codi_cta = ?
)
SELECT FILIAL, min(DATA) DATA_MIN, max(DATA) DATA_MAX, sum(VALOR) TOTAL, NUMERO
FROM Busca_historico
WHERE NUMERO <> 0
GROUP BY NUMERO, FILIAL
ORDER BY NUMERO
"""